import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    
    # Flask
    SECRET_KEY = os.getenv('API_SECRET_KEY', 'dev-secret-key')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Supabase (REST API)
    SUPABASE_URL = os.getenv('SUPABASE_URL', '')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY', '')

    # Cloudinary
    CLOUDINARY_URL = os.getenv('CLOUDINARY_URL', '')
    CLOUDINARY_UPLOAD_PRESET = os.getenv('CLOUDINARY_UPLOAD_PRESET', '')
    
    # PostgreSQL - Support both connection string and individual params
    POSTGRES_CONNECTION_STRING = os.getenv('POSTGRES_CONNECTION_STRING', '')
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
    POSTGRES_DB = os.getenv('POSTGRES_DB', 'billing_db')
    POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')
    
    # Neo4j
    NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
    NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', '')
    
    # OpenAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    
    # Google Gemini
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyADOyN7mFxYE9HLTuR44KEjH21LRwyQR9A')
    
    # Stripe
    STRIPE_API_KEY = os.getenv('STRIPE_API_KEY', '')
    STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '')
    
    # WhatsApp
    WHATSAPP_PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID', '')
    WHATSAPP_ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN', '')
    
    # Discord
    DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL', '')
    
    # Auth0
    AUTH0_DOMAIN = os.getenv('AUTH0_DOMAIN', '')
    AUTH0_API_IDENTIFIER = os.getenv('AUTH0_API_IDENTIFIER', '')
    
    # Webhook Auth
    HEADER_AUTH_TOKEN = os.getenv('HEADER_AUTH_TOKEN', '')
