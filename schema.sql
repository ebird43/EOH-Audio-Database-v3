-- Database Schema for Adidam Audio Recordings

-- Main table for recordings
CREATE TABLE recordings (
    id INTEGER PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    date_recorded DATE,
    duration TIME,
    file_path VARCHAR(255),
    file_size INTEGER,
    audio_format VARCHAR(50),
    bitrate INTEGER,
    sample_rate INTEGER,
    date_added DATE,
    is_public BOOLEAN DEFAULT true,
    play_count INTEGER DEFAULT 0,
    download_count INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS essays (
    id INTEGER PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    book_id INTEGER REFERENCES books(id),
    essay_number VARCHAR(50),
    display_order INTEGER DEFAULT 0
);

-- Categories/tags for the recordings
CREATE TABLE IF NOT EXISTS recordings (
    id INTEGER PRIMARY KEY,
    essay_id INTEGER REFERENCES essays(id),
    title VARCHAR(255),
    reciter VARCHAR(100),
    recorded_date DATE,
    duration TIME,
    file_path VARCHAR(255),
    date_added DATE DEFAULT CURRENT_DATE
);

-- Junction table for many-to-many relationship between recordings and categories
CREATE TABLE recording_categories (
    recording_id INTEGER REFERENCES recordings(id),
    category_id INTEGER REFERENCES categories(id),
    PRIMARY KEY (recording_id, category_id)
);

-- Table for speakers/presenters
CREATE TABLE speakers (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    bio TEXT
);

-- Table for linking recordings to speakers (many-to-many)
CREATE TABLE recording_speakers (
    recording_id INTEGER REFERENCES recordings(id),
    speaker_id INTEGER REFERENCES speakers(id),
    PRIMARY KEY (recording_id, speaker_id)
);

-- Table for locations where recordings were made
CREATE TABLE locations (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT
);

-- Table for series or collections
CREATE TABLE series (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT
);

-- Table for transcripts
CREATE TABLE transcripts (
    id INTEGER PRIMARY KEY,
    recording_id INTEGER REFERENCES recordings(id),
    text TEXT,
    is_complete BOOLEAN DEFAULT false,
    language VARCHAR(50) DEFAULT 'English'
);

-- Table for keywords and search terms
CREATE TABLE keywords (
    id INTEGER PRIMARY KEY,
    recording_id INTEGER REFERENCES recordings(id),
    keyword VARCHAR(100) NOT NULL
);

-- Table for user favorites and playlists
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT false,
    date_registered DATE NOT NULL
);

CREATE TABLE playlists (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_public BOOLEAN DEFAULT false,
    date_created DATE NOT NULL
);

CREATE TABLE playlist_recordings (
    playlist_id INTEGER REFERENCES playlists(id),
    recording_id INTEGER REFERENCES recordings(id),
    position INTEGER NOT NULL,
    date_added DATE NOT NULL,
    PRIMARY KEY (playlist_id, recording_id)
);

CREATE TABLE user_favorites (
    user_id INTEGER REFERENCES users(id),
    recording_id INTEGER REFERENCES recordings(id),
    date_added DATE NOT NULL,
    PRIMARY KEY (user_id, recording_id)
);

-- Table for user notes on recordings
CREATE TABLE user_notes (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    recording_id INTEGER REFERENCES recordings(id),
    note TEXT NOT NULL,
    date_added DATE NOT NULL
);

-- Table for metadata specific to Adidam recordings
CREATE TABLE adidam_metadata (
    recording_id INTEGER PRIMARY KEY REFERENCES recordings(id),
    discourse_type VARCHAR(100),
    event_type VARCHAR(100),
    year_period VARCHAR(50),
    related_texts TEXT,
    special_notes TEXT
);

-- Indexes for faster searches
CREATE INDEX idx_recordings_title ON recordings(title);
CREATE INDEX idx_recordings_date ON recordings(date_recorded);
CREATE INDEX idx_categories_name ON categories(name);
CREATE INDEX idx_speakers_name ON speakers(name);
CREATE INDEX idx_keywords_keyword ON keywords(keyword);
CREATE INDEX idx_transcripts_recording ON transcripts(recording_id);
-- SQLite doesn't support FULLTEXT INDEX