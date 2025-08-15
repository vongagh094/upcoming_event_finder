# Domain excludes, keywords, site configs

# Social media and general platforms to filter out
EXCLUDE_DOMAINS = {
    'facebook.com',
    'twitter.com',
    'x.com',
    'linkedin.com',
    'instagram.com',
    'youtube.com',
    'tiktok.com',
    'reddit.com',
    'pinterest.com',
    'snapchat.com',
    'discord.com',
    'telegram.org',
    'whatsapp.com',
    'wikipedia.org',
    'amazon.com',
    'ebay.com',
    'craigslist.org',
    'indeed.com',
    'glassdoor.com',
    'monster.com',
    'careerbuilder.com'
}


# Search query templates for DuckDuckGo
QUERY_TEMPLATES = [
    '"{}" upcoming events 2025',
    '"{}" keynote conference',
    '"{}" webinar workshop',
    '"{}" speaking events',
    'site:eventbrite.com "{}"',
    'site:meetup.com "{}"'
]

extract_schema = {
  "type": "object",
  "properties": {
    "events": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "event_name": { "type": "string" },
          "date": { "type": "string", "description": "ISO 8601 date/time" },
          "location": {
            "type": "object",
            "properties": {
              "name": { "type": "string" },
              "address": { "type": "string" },
              "city": { "type": "string" },
              "country": { "type": "string" }
            },
            "required": ["name"]
          },
          "url": { "type": "string" },
          "speakers": { "type": "array", "items": { "type": "string" } },
          "event_type": { "type": "string", "enum": ["in_person", "online", "N/A"] }
        },
        "required": ["event_name", "url", "speakers", "event_type", "date", "location"]
      }
    }
  },
  "required": ["events"]
}