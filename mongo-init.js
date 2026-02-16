// MongoDB initialization script
// Creates application user and database

db = db.getSiblingDB(process.env.MONGO_INITDB_DATABASE || 'socialfi_db');

// Create indexes that should exist from the start
db.createCollection('users');
db.createCollection('unified_posts');
db.createCollection('markets');
db.createCollection('positions');
db.createCollection('trades');
db.createCollection('challenges');

print('MongoDB initialized for SocialFi');
