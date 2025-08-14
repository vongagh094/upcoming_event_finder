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

# Event-related search terms in priority order
KEYWORDS = [
    'speaking',
    'keynote',
    'conference',
    'event',
    'webinar',
    'workshop',
    'seminar',
    'presentation',
    'talk',
    'summit',
    'meetup',
    'panel'
]


# Search query templates for DuckDuckGo
DDG_TEMPLATES = [
    '"{}" upcoming event 2025',
    '"{}" keynote conference',
    '"{}" webinar workshop',
    '"{}" speaking event',
    'site:eventbrite.com "{}"',
    'site:meetup.com "{}"'
]