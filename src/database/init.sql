-- Database initialization script for untitled-api-project
-- Wine database schema

-- Enable UUID extension for generating unique IDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table - basic user management
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Wine regions table
CREATE TABLE IF NOT EXISTS wine_regions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    country VARCHAR(100) NOT NULL,
    description TEXT,
    climate VARCHAR(100),
    soil_type VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Wines table - stores wine information
CREATE TABLE IF NOT EXISTS wines (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    vintage INTEGER NOT NULL,
    region_id UUID NOT NULL REFERENCES wine_regions(id) ON DELETE RESTRICT,
    grape_variety VARCHAR(255),
    winery VARCHAR(255),
    alcohol_percentage DECIMAL(4,2),
    price DECIMAL(10,2),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- Composite unique constraint for wine name + vintage + region
    UNIQUE(name, vintage, region_id)
);

-- User wine collection table - many-to-many relationship
CREATE TABLE IF NOT EXISTS user_wines (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    wine_id UUID NOT NULL REFERENCES wines(id) ON DELETE CASCADE,
    quantity INTEGER DEFAULT 1,
    purchase_date DATE,
    purchase_price DECIMAL(10,2),
    storage_location VARCHAR(255),
    notes TEXT,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- Prevent duplicate entries for same user and wine
    UNIQUE(user_id, wine_id)
);

-- Wine tastings table - user wine experiences
CREATE TABLE IF NOT EXISTS wine_tastings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    wine_id UUID NOT NULL REFERENCES wines(id) ON DELETE CASCADE,
    tasting_date DATE NOT NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    notes TEXT,
    aroma_notes TEXT,
    taste_notes TEXT,
    finish_notes TEXT,
    overall_impression TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_wines_name ON wines(name);
CREATE INDEX IF NOT EXISTS idx_wines_vintage ON wines(vintage);
CREATE INDEX IF NOT EXISTS idx_wines_region_id ON wines(region_id);
CREATE INDEX IF NOT EXISTS idx_wines_winery ON wines(winery);
CREATE INDEX IF NOT EXISTS idx_user_wines_user_id ON user_wines(user_id);
CREATE INDEX IF NOT EXISTS idx_user_wines_wine_id ON user_wines(wine_id);
CREATE INDEX IF NOT EXISTS idx_wine_tastings_user_id ON wine_tastings(user_id);
CREATE INDEX IF NOT EXISTS idx_wine_tastings_wine_id ON wine_tastings(wine_id);
CREATE INDEX IF NOT EXISTS idx_wine_tastings_tasting_date ON wine_tastings(tasting_date);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply the trigger to tables with updated_at columns
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_wine_regions_updated_at BEFORE UPDATE ON wine_regions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_wines_updated_at BEFORE UPDATE ON wines
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_wines_updated_at BEFORE UPDATE ON user_wines
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_wine_tastings_updated_at BEFORE UPDATE ON wine_tastings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample wine regions
INSERT INTO wine_regions (name, country, description, climate, soil_type) VALUES 
    ('Bordeaux', 'France', 'Famous wine region known for red blends', 'Maritime', 'Gravel and clay'),
    ('Tuscany', 'Italy', 'Home to Chianti and Brunello wines', 'Mediterranean', 'Limestone and clay'),
    ('Napa Valley', 'United States', 'Premium California wine region', 'Mediterranean', 'Volcanic and alluvial'),
    ('Rioja', 'Spain', 'Spain''s most famous wine region', 'Continental', 'Limestone and clay'),
    ('Barossa Valley', 'Australia', 'Known for Shiraz wines', 'Mediterranean', 'Red brown earth')
ON CONFLICT (name) DO NOTHING;

-- Insert sample wines
INSERT INTO wines (name, vintage, region_id, grape_variety, winery, alcohol_percentage, price, description) VALUES 
    ('Château Margaux', 2015, (SELECT id FROM wine_regions WHERE name = 'Bordeaux'), 'Cabernet Sauvignon Blend', 'Château Margaux', 13.5, 1500.00, 'Exceptional vintage with complex aromas'),
    ('Sassicaia', 2018, (SELECT id FROM wine_regions WHERE name = 'Tuscany'), 'Cabernet Sauvignon', 'Tenuta San Guido', 14.0, 800.00, 'Super Tuscan with elegant structure'),
    ('Opus One', 2016, (SELECT id FROM wine_regions WHERE name = 'Napa Valley'), 'Cabernet Sauvignon Blend', 'Opus One Winery', 14.5, 1200.00, 'Bordeaux-style blend from Napa'),
    ('Vega Sicilia Unico', 2012, (SELECT id FROM wine_regions WHERE name = 'Rioja'), 'Tempranillo', 'Vega Sicilia', 14.0, 600.00, 'Spain''s most prestigious wine'),
    ('Penfolds Grange', 2014, (SELECT id FROM wine_regions WHERE name = 'Barossa Valley'), 'Shiraz', 'Penfolds', 14.5, 900.00, 'Australia''s most famous wine')
ON CONFLICT (name, vintage, region_id) DO NOTHING;
