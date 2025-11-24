from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Loads and validates all environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding='utf-8', 
        extra='ignore'
    )

    GOOGLE_API_KEY: str
    TAVILY_API_KEY: str
    PINECONE_API_KEY: str
    PINECONE_INDEX_NAME: str = "sturdy-study" 

settings = Settings()