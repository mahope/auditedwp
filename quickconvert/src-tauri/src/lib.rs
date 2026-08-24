use serde_json::Value;

/// Format converter: parses input into JSON Value, then serializes to output format
/// All heavy lifting via serde_json and serde_yaml/toml/csv/quick-xml crates

fn parse_to_json(text: &str, format: &str) -> Result<Value, String> {
    match format {
        "json" => serde_json::from_str(text).map_err(|e| e.to_string()),
        "yaml" => {
            let v: serde_yaml::Value = serde_yaml::from_str(text).map_err(|e| e.to_string())?;
            yaml_val_to_json(v)
        }
        "toml" => {
            let v: toml::Value = toml::from_str(text).map_err(|e| e.to_string())?;
            toml_val_to_json(&v)
        }
        "csv" => {
            let mut rdr = csv::ReaderBuilder::new()
                .has_headers(true)
                .flexible(true)
                .from_reader(text.as_bytes());
            let headers: Vec<String> = rdr
                .headers()
                .map_err(|e| e.to_string())?
                .iter()
                .map(|h| h.to_string())
                .collect();
            let mut records = Vec::new();
            for result in rdr.records() {
                let rec = result.map_err(|e| e.to_string())?;
                let mut map = serde_json::Map::new();
                for (i, field) in rec.iter().enumerate() {
                    if i < headers.len() {
                        map.insert(headers[i].clone(), Value::String(field.to_string()));
                    }
                }
                records.push(Value::Object(map));
            }
            Ok(Value::Array(records))
        }
        "xml" => {
            let mut reader = quick_xml::Reader::from_str(text);
            // trim text manually in Text event handler
            let mut depth = 0usize;
            let mut path = Vec::new();
            let mut text_buf = String::new();
            let mut result_map: Option<serde_json::Map<String, Value>> = None;
            let mut stack: Vec<(String, serde_json::Map<String, Value>)> = Vec::new();

            loop {
                match reader.read_event() {
                    Ok(quick_xml::events::Event::Start(ref e)) => {
                        let name = String::from_utf8_lossy(e.name().as_ref()).to_string();
                        let mut attrs = serde_json::Map::new();
                        for attr in e.attributes().flatten() {
                            let k = format!("@{}", String::from_utf8_lossy(attr.key.as_ref()));
                            let v = attr.decode_and_unescape_value(reader.decoder()).unwrap_or_default().into_owned();
                            attrs.insert(k, Value::String(v));
                        }
                        stack.push((name.clone(), attrs));
                        path.push(name);
                        text_buf.clear();
                        depth += 1;
                    }
                    Ok(quick_xml::events::Event::End(_)) => {
                        depth -= 1;
                        let child_name = path.pop().unwrap_or_default();

                        // Build current element as object
                        if let Some((_name, mut attrs)) = stack.pop() {
                            let trimmed = text_buf.trim().to_string();
                            if !trimmed.is_empty() {
                                attrs.insert("#text".into(), Value::String(trimmed));
                            }
                            text_buf.clear();

                            let elem = if attrs.is_empty() {
                                Value::String(String::new())
                            } else if attrs.len() == 1 && attrs.contains_key("#text") {
                                attrs.remove("#text").unwrap()
                            } else {
                                Value::Object(attrs)
                            };

                            if let Some((_pname, parent)) = stack.last_mut() {
                                // Merge into parent
                                let existing = parent.entry(child_name).or_insert(Value::Array(Vec::new()));
                                match existing {
                                    Value::Array(arr) => arr.push(elem),
                                    Value::Null => *existing = elem,
                                    other => {
                                        let old = std::mem::replace(other, Value::Array(Vec::new()));
                                        if let Value::Array(ref mut arr) = other {
                                            arr.push(old);
                                            arr.push(elem);
                                        }
                                    }
                                }
                            } else {
                                let mut root = serde_json::Map::new();
                                root.insert(child_name, elem);
                                result_map = Some(root);
                            }
                        }
                    }
                    Ok(quick_xml::events::Event::Text(ref e)) => {
                        if let Ok(t) = e.unescape() {
                            text_buf.push_str(&t);
                        }
                    }
                    Ok(quick_xml::events::Event::Eof) => break,
                    Err(e) => return Err(format!("XML error: {}", e)),
                    _ => {}
                }
            }

            result_map
                .map(Value::Object)
                .ok_or_else(|| "Empty XML".to_string())
        }
        _ => Err(format!("Unsupported format: {}", format)),
    }
}

fn yaml_val_to_json(v: serde_yaml::Value) -> Result<Value, String> {
    Ok(match v {
        serde_yaml::Value::Null => Value::Null,
        serde_yaml::Value::Bool(b) => Value::Bool(b),
        serde_yaml::Value::Number(n) => {
            if let Some(i) = n.as_i64() {
                Value::Number(i.into())
            } else if let Some(f) = n.as_f64() {
                serde_json::Number::from_f64(f).map(Value::Number).unwrap_or(Value::Null)
            } else {
                Value::String(n.to_string())
            }
        }
        serde_yaml::Value::String(s) => Value::String(s),
        serde_yaml::Value::Sequence(seq) => {
            let items: Result<Vec<Value>, String> = seq.into_iter().map(|v| yaml_val_to_json(v)).collect();
            Value::Array(items?)
        }
        serde_yaml::Value::Mapping(map) => {
            let mut obj = serde_json::Map::new();
            for (k, v) in map {
                let key = match k {
                    serde_yaml::Value::String(s) => s,
                    other => format!("{:?}", other),
                };
                obj.insert(key, yaml_val_to_json(v)?);
            }
            Value::Object(obj)
        }
        _ => Value::String(format!("{:?}", v)),
    })
}

fn toml_val_to_json(v: &toml::Value) -> Result<Value, String> {
    Ok(match v {
        toml::Value::String(s) => Value::String(s.clone()),
        toml::Value::Integer(i) => Value::Number((*i).into()),
        toml::Value::Float(f) => serde_json::Number::from_f64(*f).map(Value::Number).unwrap_or(Value::Null),
        toml::Value::Boolean(b) => Value::Bool(*b),
        toml::Value::Datetime(dt) => Value::String(dt.to_string()),
        toml::Value::Array(arr) => {
            let items: Result<Vec<Value>, String> = arr.iter().map(|v| toml_val_to_json(v)).collect();
            Value::Array(items?)
        }
        toml::Value::Table(table) => {
            let mut obj = serde_json::Map::new();
            for (k, v) in table {
                obj.insert(k.clone(), toml_val_to_json(v)?);
            }
            Value::Object(obj)
        }
    })
}

fn json_to_yaml_val(v: &Value) -> serde_yaml::Value {
    match v {
        Value::Null => serde_yaml::Value::Null,
        Value::Bool(b) => serde_yaml::Value::Bool(*b),
        Value::Number(n) => {
            if let Some(i) = n.as_i64() {
                serde_yaml::Value::Number(serde_yaml::Number::from(i))
            } else if let Some(f) = n.as_f64() {
                serde_yaml::Value::Number(serde_yaml::Number::from(f))
            } else {
                serde_yaml::Value::String(n.to_string())
            }
        }
        Value::String(s) => serde_yaml::Value::String(s.clone()),
        Value::Array(arr) => serde_yaml::Value::Sequence(arr.iter().map(json_to_yaml_val).collect()),
        Value::Object(map) => {
            let mut m = serde_yaml::Mapping::new();
            for (k, v) in map {
                m.insert(serde_yaml::Value::String(k.clone()), json_to_yaml_val(v));
            }
            serde_yaml::Value::Mapping(m)
        }
    }
}

fn json_to_toml_val(v: &Value) -> toml::Value {
    match v {
        Value::Null => toml::Value::String("null".into()),
        Value::Bool(b) => toml::Value::Boolean(*b),
        Value::Number(n) => {
            if let Some(i) = n.as_i64() {
                toml::Value::Integer(i)
            } else if let Some(f) = n.as_f64() {
                toml::Value::Float(f)
            } else {
                toml::Value::String(n.to_string())
            }
        }
        Value::String(s) => toml::Value::String(s.clone()),
        Value::Array(arr) => toml::Value::Array(arr.iter().map(json_to_toml_val).collect()),
        Value::Object(map) => {
            let mut table = toml::value::Table::new();
            for (k, v) in map {
                table.insert(k.clone(), json_to_toml_val(v));
            }
            toml::Value::Table(table)
        }
    }
}

fn json_to_xml_str(v: &Value, name: &str, depth: usize) -> String {
    let indent = "\n".to_string() + &"  ".repeat(depth);
    let close = "\n".to_string() + &"  ".repeat(depth);

    match v {
        Value::Null => format!("{indent}<{name}/>"),
        Value::Bool(b) => format!("{indent}<{name}>{b}</{name}>{close}"),
        Value::Number(n) => format!("{indent}<{name}>{n}</{name}>{close}"),
        Value::String(s) => {
            let e = s.replace('&', "&amp;").replace('<', "&lt;").replace('>', "&gt;").replace('"', "&quot;");
            format!("{indent}<{name}>{e}</{name}>{close}")
        }
        Value::Array(arr) => {
            arr.iter().map(|item| json_to_xml_str(item, name, depth)).collect::<Vec<_>>().join("")
        }
        Value::Object(map) => {
            let mut attrs = String::new();
            let mut kids = Vec::new();
            for (k, v) in map {
                if k.starts_with('@') {
                    let val = match v { Value::String(s) => s.clone(), other => other.to_string() };
                    attrs.push_str(&format!(" {}=\"{}\"", &k[1..], val.replace('&', "&amp;").replace('"', "&quot;")));
                } else if k == "#text" {
                    if let Some(s) = v.as_str() {
                        return format!("{indent}<{name}{attrs}>{}</{name}>{close}", s.replace('&', "&amp;").replace('<', "&lt;").replace('>', "&gt;"));
                    }
                } else {
                    kids.push((k, v));
                }
            }
            if kids.is_empty() {
                format!("{indent}<{name}{attrs}/>")
            } else {
                let inner: String = kids.iter().map(|(k, v)| json_to_xml_str(v, k, depth + 1)).collect();
                format!("{indent}<{name}{attrs}>{inner}\n{indent}</{name}>{close}")
            }
        }
    }
}

#[tauri::command]
fn detect(text: String) -> Result<String, String> {
    let t = text.trim();
    if t.is_empty() { return Err("empty".into()); }

    if (t.starts_with('{') || t.starts_with('[')) && (t.ends_with('}') || t.ends_with(']')) {
        if serde_json::from_str::<Value>(t).is_ok() { return Ok("json".into()); }
    }
    if t.starts_with('<') && (t.contains("</") || t.ends_with("/>")) {
        // Quick XML check
        return Ok("xml".into());
    }
    if let Some(line) = t.lines().find(|l| !l.trim().is_empty()) {
        let l = line.trim();
        if l.starts_with('[') && l.ends_with(']') && l.len() > 2 {
            return Ok("toml".into());
        }
        if l.len() > 3 && l.contains(':') && !l.starts_with('{') && !l.starts_with('[') {
            if serde_yaml::from_str::<serde_yaml::Value>(t).is_ok() {
                return Ok("yaml".into());
            }
        }
    }
    // Check YAML with --- prefix
    if t.starts_with("---") {
        if serde_yaml::from_str::<serde_yaml::Value>(t).is_ok() {
            return Ok("yaml".into());
        }
    }
    // CSV check
    if t.contains(',') {
        let lines: Vec<&str> = t.lines().filter(|l| !l.trim().is_empty()).collect();
        if lines.len() >= 2 {
            let cols = lines[0].split(',').count();
            if cols >= 2 && lines[1..].iter().all(|l| l.split(',').count() >= cols / 2) {
                return Ok("csv".into());
            }
        }
    }
    Err("unknown".into())
}

#[tauri::command]
fn convert(input: String, from: String, to: String) -> Result<String, String> {
    let source = if from == "auto" { detect(input.clone())? } else { from.clone() };
    let value = parse_to_json(&input, &source)?;

    match to.as_str() {
        "json" => serde_json::to_string_pretty(&value).map_err(|e| e.to_string()),
        "yaml" => {
            let yv = json_to_yaml_val(&value);
            serde_yaml::to_string(&yv).map_err(|e| e.to_string())
        }
        "toml" => {
            let tv = json_to_toml_val(&value);
            toml::to_string(&tv).map_err(|e| e.to_string())
        }
        "csv" => {
            let items = match &value {
                Value::Array(arr) => arr,
                _ => return Err("CSV output requires an array of objects".into()),
            };
            if items.is_empty() { return Ok(String::new()); }
            let mut keys: Vec<String> = Vec::new();
            for item in items {
                if let Value::Object(obj) = item {
                    for k in obj.keys() {
                        if !keys.contains(k) { keys.push(k.clone()); }
                    }
                }
            }
            let mut wtr = csv::Writer::from_writer(Vec::new());
            wtr.write_record(&keys).map_err(|e| e.to_string())?;
            for item in items {
                if let Value::Object(obj) = item {
                    let rec: Vec<String> = keys.iter().map(|k| {
                        obj.get(k).map(|v| match v {
                            Value::String(s) => s.clone(),
                            other => other.to_string(),
                        }).unwrap_or_default()
                    }).collect();
                    wtr.write_record(&rec).map_err(|e| e.to_string())?;
                }
            }
            wtr.flush().map_err(|e| e.to_string())?;
            let bytes = wtr.into_inner().map_err(|e| e.to_string())?;
            String::from_utf8(bytes).map_err(|e| e.to_string())
        }
        "xml" => {
            let xml = json_to_xml_str(&value, "root", 0);
            Ok(xml.trim().to_string())
        }
        _ => Err(format!("Unsupported target format: {}", to)),
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![convert, detect])
        .setup(|app| {
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}