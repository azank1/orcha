"""OAuth authentication tool for Google (TradingView access)"""
import structlog
from typing import Dict, Any
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from ..config import settings

logger = structlog.get_logger()

# OAuth scopes required
SCOPES = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile'
]


def get_oauth_url() -> str:
    """
    Generate Google OAuth authorization URL
    
    Returns:
        Authorization URL for user to visit
    """
    logger.info("generate_oauth_url")
    
    try:
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.google_oauth_client_id,
                    "client_secret": settings.google_oauth_client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.google_oauth_redirect_uri]
                }
            },
            scopes=SCOPES
        )
        
        flow.redirect_uri = settings.google_oauth_redirect_uri
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        logger.info("oauth_url_generated", state=state)
        
        return authorization_url
        
    except Exception as e:
        logger.error("oauth_url_error", error=str(e))
        raise Exception(f"Failed to generate OAuth URL: {str(e)}")


async def exchange_oauth_code(code: str) -> Dict[str, Any]:
    """
    Exchange authorization code for access token
    
    Args:
        code: Authorization code from OAuth callback
        
    Returns:
        Dict with access_token and refresh_token
    """
    logger.info("exchange_oauth_code")
    
    try:
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.google_oauth_client_id,
                    "client_secret": settings.google_oauth_client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.google_oauth_redirect_uri]
                }
            },
            scopes=SCOPES
        )
        
        flow.redirect_uri = settings.google_oauth_redirect_uri
        
        # Exchange code for token
        flow.fetch_token(code=code)
        
        credentials = flow.credentials
        
        token_data = {
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes,
            "expires_in": 3600  # Typically 1 hour
        }
        
        logger.info("oauth_token_exchanged")
        
        return token_data
        
    except Exception as e:
        logger.error("oauth_exchange_error", error=str(e))
        raise Exception(f"Failed to exchange OAuth code: {str(e)}")


async def refresh_oauth_token(refresh_token: str) -> Dict[str, Any]:
    """
    Refresh an expired OAuth token
    
    Args:
        refresh_token: Refresh token from previous authorization
        
    Returns:
        Dict with new access_token
    """
    logger.info("refresh_oauth_token")
    
    try:
        credentials = Credentials(
            None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.google_oauth_client_id,
            client_secret=settings.google_oauth_client_secret
        )
        
        # Refresh the token
        credentials.refresh(Request())
        
        token_data = {
            "access_token": credentials.token,
            "expires_in": 3600
        }
        
        logger.info("oauth_token_refreshed")
        
        return token_data
        
    except Exception as e:
        logger.error("oauth_refresh_error", error=str(e))
        raise Exception(f"Failed to refresh OAuth token: {str(e)}")
