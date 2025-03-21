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
            # Create shared update_updated_at function
            cur.execute("""
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = NOW();
                    RETURN NEW;
                END;
                $$ language 'plpgsql';
            """)
            
            # 1. PATIENTS TABLE
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
            
            cur.execute("""
                DROP TRIGGER IF EXISTS update_patients_updated_at ON patients;
            """)
            
            cur.execute("""
                CREATE TRIGGER update_patients_updated_at
                BEFORE UPDATE ON patients
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
            """)
            
            # 2. MENTAL HEALTH CONSULTANTS TABLE
            cur.execute("""
                CREATE TABLE IF NOT EXISTS consultants (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    specialization VARCHAR(100) NOT NULL,
                    qualifications TEXT,
                    contact_info JSONB,
                    availability JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cur.execute("""
                DROP TRIGGER IF EXISTS update_consultants_updated_at ON consultants;
            """)
            
            cur.execute("""
                CREATE TRIGGER update_consultants_updated_at
                BEFORE UPDATE ON consultants
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
            """)
            
            # 3. PSYCHIATRISTS TABLE
            cur.execute("""
                CREATE TABLE IF NOT EXISTS psychiatrists (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    specialization VARCHAR(100) NOT NULL,
                    qualifications TEXT,
                    hospital VARCHAR(100),
                    contact_info JSONB,
                    availability JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cur.execute("""
                DROP TRIGGER IF EXISTS update_psychiatrists_updated_at ON psychiatrists;
            """)
            
            cur.execute("""
                CREATE TRIGGER update_psychiatrists_updated_at
                BEFORE UPDATE ON psychiatrists
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
            """)
            
            # 4. SCREENING TOOLS TABLE
            cur.execute("""
                CREATE TABLE IF NOT EXISTS screening_tools (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    questions JSONB NOT NULL,
                    scoring_method TEXT,
                    interpretation_guide TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cur.execute("""
                DROP TRIGGER IF EXISTS update_screening_tools_updated_at ON screening_tools;
            """)
            
            cur.execute("""
                CREATE TRIGGER update_screening_tools_updated_at
                BEFORE UPDATE ON screening_tools
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
            """)
            
            # 5. LISTENING TEMPLATES TABLE
            cur.execute("""
                CREATE TABLE IF NOT EXISTS listening_templates (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    questions JSONB NOT NULL,
                    guidelines TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cur.execute("""
                DROP TRIGGER IF EXISTS update_listening_templates_updated_at ON listening_templates;
            """)
            
            cur.execute("""
                CREATE TRIGGER update_listening_templates_updated_at
                BEFORE UPDATE ON listening_templates
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
            """)
            
            # 6. REFERRALS TABLE
            cur.execute("""
                CREATE TABLE IF NOT EXISTS referrals (
                    id SERIAL PRIMARY KEY,
                    patient_id VARCHAR(50) REFERENCES patients(id),
                    consultant_id INTEGER REFERENCES consultants(id) NULL,
                    psychiatrist_id INTEGER REFERENCES psychiatrists(id) NULL,
                    reason TEXT NOT NULL,
                    notes TEXT,
                    status VARCHAR(20) DEFAULT 'pending',
                    appointment_date TIMESTAMP NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cur.execute("""
                DROP TRIGGER IF EXISTS update_referrals_updated_at ON referrals;
            """)
            
            cur.execute("""
                CREATE TRIGGER update_referrals_updated_at
                BEFORE UPDATE ON referrals
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
            if version and len(version) > 0:
                return True, f"Successfully connected to PostgreSQL: {version[0]}"
            else:
                return True, "Successfully connected to PostgreSQL"
    except Exception as e:
        return False, f"Error testing database: {e}"
    finally:
        if conn:
            conn.close()