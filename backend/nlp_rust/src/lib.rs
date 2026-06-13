use pyo3::prelude::*;
use regex::Regex;
use lazy_static::lazy_static;
use ahash::AHashMap;

lazy_static! {
    // 预编译正则表达式，提升性能
    static ref URL_RE: Regex = Regex::new(r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+").unwrap();
    static ref AT_RE: Regex = Regex::new(r"@[\w\-]+").unwrap();
    static ref HASHTAG_RE: Regex = Regex::new(r"#[^#]+#").unwrap();
    static ref EMOJI_RE: Regex = Regex::new(r"\[.*?\]").unwrap();
    static ref HTML_RE: Regex = Regex::new(r"<[^>]+>").unwrap();
    static ref WHITESPACE_RE: Regex = Regex::new(r"\s+").unwrap();
    static ref CHINESE_RE: Regex = Regex::new(r"[\u{4e00}-\u{9fff}]").unwrap();
}

/// 清理文本
#[pyfunction]
fn clean_text(text: &str) -> PyResult<String> {
    if text.is_empty() {
        return Ok(String::new());
    }

    let mut result = text.to_string();
    result = URL_RE.replace_all(&result, "").to_string();
    result = AT_RE.replace_all(&result, "").to_string();
    result = HASHTAG_RE.replace_all(&result, "").to_string();
    result = EMOJI_RE.replace_all(&result, "").to_string();
    result = HTML_RE.replace_all(&result, "").to_string();
    result = WHITESPACE_RE.replace_all(&result, " ").to_string();

    Ok(result.trim().to_string())
}

/// 批量清理文本
#[pyfunction]
fn clean_texts(texts: Vec<&str>) -> PyResult<Vec<String>> {
    Ok(texts.iter().map(|&text| {
        clean_text(text).unwrap_or_else(|_| String::new())
    }).collect())
}

/// 词频统计
#[pyfunction]
fn word_frequency(
    words: Vec<&str>,
    stopwords: Vec<&str>,
    min_length: usize
) -> PyResult<AHashMap<String, usize>> {
    let stopwords_set: ahash::AHashSet<&str> = stopwords.into_iter().collect();
    let mut freq: AHashMap<String, usize> = AHashMap::new();

    for word in words {
        let word = word.trim();
        if !word.is_empty()
            && word.len() >= min_length
            && !stopwords_set.contains(word)
            && CHINESE_RE.is_match(word)
        {
            *freq.entry(word.to_string()).or_insert(0) += 1;
        }
    }

    Ok(freq)
}

#[pymodule]
fn nlp_rust(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(clean_text, m)?)?;
    m.add_function(wrap_pyfunction!(clean_texts, m)?)?;
    m.add_function(wrap_pyfunction!(word_frequency, m)?)?;
    Ok(())
}
