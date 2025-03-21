import os
import psycopg2
from sqlalchemy import create_engine, text
import streamlit as st

# Database connection parameters
DB_HOST = "pg-smpn9mlg-smpn9mlg-aplikasi-bk.g.aivencloud.com"
DB_PORT = "20360"
DB_NAME = "defaultdb"
DB_USER = "avnadmin"
DB_PASSWORD = "AVNS_KezbHs7zMd6Y3pjxPoq"
DB_SSL_MODE = "require"
DB_SSL_CERT = "postgresql-cert.pem"

# Get the absolute path to the certificate file
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
cert_path = os.path.join(root_dir, DB_SSL_CERT)

def get_connection_string():
    """Get the connection string for PostgreSQL"""
    return f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode={DB_SSL_MODE}&sslrootcert={cert_path}"

def get_db_connection():
    """Get a connection to the PostgreSQL database"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            sslmode=DB_SSL_MODE,
            sslrootcert=cert_path
        )
        return conn
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        return None

def get_db_engine():
    """Get SQLAlchemy engine for database operations"""
    try:
        engine = create_engine(get_connection_string())
        return engine
    except Exception as e:
        st.error(f"Error creating database engine: {e}")
        return None

def initialize_database():
    """Initialize database tables if they don't exist"""
    
    # Check if connection can be established
    conn = get_db_connection()
    if conn is None:
        st.error("Failed to connect to the database. Check your connection parameters.")
        return False
    
    try:
        # Create patients table
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS patients (
                    id VARCHAR(50) PRIMARY KEY,
                    data JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create an index on the id field for faster lookups
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_patients_id ON patients(id)
            """)
            
            # Create a trigger to automatically update the updated_at field
            cur.execute("""
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = NOW();
                    RETURN NEW;
                END;
                $$ language 'plpgsql';
            """)
            
            cur.execute("""
                DROP TRIGGER IF EXISTS update_patients_updated_at ON patients;
            """)
            
            cur.execute("""
                CREATE TRIGGER update_patients_updated_at
                BEFORE UPDATE ON patients
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
            """)
            
            # Commit the changes
            conn.commit()
        
        return True
    except Exception as e:
        st.error(f"Error initializing database: {e}")
        return False
    finally:
        if conn:
            conn.close()

def test_database_connection():
    """Test the database connection and return status"""
    conn = get_db_connection()
    if conn is None:
        return False, "Failed to connect to the database"
    
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT version()")
            version = cur.fetchone()
            return True, f"Successfully connected to PostgreSQL: {version[0]}"
    except Exception as e:
        return False, f"Error testing database: {e}"
    finally:
        if conn:
            conn.close()