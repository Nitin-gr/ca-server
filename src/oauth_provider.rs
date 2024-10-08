use reqwest::{
    header::{HeaderMap, USER_AGENT},
    Client,
};
use serde_json::Value;
use std::env;
use std::error::Error;

pub async fn get_email_from_provider(
    access_token: String,
    provider: &str,
) -> Result<String, Box<dyn Error>> {
    let client = Client::builder().build()?;

    let mut headers = HeaderMap::new();
    headers.insert("Authorization", format!("Bearer {}", access_token).parse()?);

    let url = match provider {
        "google" => env::var("GOOGLE_URL").expect("Env variable not set for Google"),
        "github" => env::var("GITHUB_URL").expect("Env variable not set for GitHub"),
        _ => return Err("Provider not supported".into()),
    };

    // Add User-Agent header for GitHub
    if provider == "github" {
        headers.insert(USER_AGENT, "sshgo".parse()?);
    }

    let response = client.get(&url).headers(headers).send().await?;

    if response.status().is_success() {
        let response_body = response.text().await?;

        let email = match provider {
            "google" => {
                let user_info: Value = serde_json::from_str(&response_body)?;
                user_info["email"].as_str().unwrap_or("").to_string()
            }
            "github" => {
                let emails: Vec<Value> = serde_json::from_str(&response_body)?;

                // Find the primary email and get its string value
                // Convert the resopnse which is an array of objects
                // into a vector and find primary email from it
                // Primary email has primary set to true in the object body
                let primary_email: String = emails
                    .into_iter()
                    .find(|e| e["primary"].as_bool().unwrap_or(false))
                    .map(|e| e["email"].as_str().unwrap_or("").to_string())
                    .unwrap_or_else(String::new);
                primary_email
            }
            _ => return Err("Provider not supported".into()),
        };

        Ok(email)
    } else {
        Err(format!("Request failed with status: {}", response.status()).into())
    }
}
