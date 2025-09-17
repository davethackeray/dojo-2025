#!/usr/bin/env python3
"""
MULTI-CONTENT TYPE PROCESSOR
InvestingDojo.co - Comprehensive Content Ingestion System

This module expands content ingestion beyond podcasts to support:
- Web pages and articles
- YouTube videos
- Ebooks (PDF, EPUB)
- Personal podcast episodes
- Newsletters
- Any text-based content

All content types are converted to transcripts for unified AI processing
through the existing CrewAI workflow.

Created for Epic 3: Multi-Content Type Ingestion System
Task 3.1: Build multi-content type processing system
"""

import os
import sys
import json
import time
import logging
import requests
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import traceback

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class ContentType(Enum):
    """Supported content types"""
    PODCAST = "podcast"
    WEBPAGE = "webpage"
    YOUTUBE = "youtube"
    EBOOK = "ebook"
    ARTICLE = "article"
    NEWSLETTER = "newsletter"
    PERSONAL_PODCAST = "personal_podcast"
    TEXT_FILE = "text_file"

@dataclass
class ContentItem:
    """Represents a piece of content to be processed"""
    content_id: str
    content_type: ContentType
    source_url: str
    title: str
    author: Optional[str] = None
    published_date: Optional[datetime] = None
    raw_content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    processing_notes: Optional[str] = None

@dataclass
class ProcessedContent:
    """Represents processed content ready for AI analysis"""
    content_id: str
    original_type: ContentType
    title: str
    transcript: str
    attribution: Dict[str, Any]
    metadata: Dict[str, Any]
    quality_score: float
    processing_timestamp: datetime

class ContentProcessor:
    """Base class for content processors"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging for content processor"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - CONTENT - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def can_process(self, content_item: ContentItem) -> bool:
        """Check if this processor can handle the content type"""
        raise NotImplementedError
    
    def process(self, content_item: ContentItem) -> ProcessedContent:
        """Process content item into transcript format"""
        raise NotImplementedError
    
    def validate_content(self, content: str) -> bool:
        """Validate that content is suitable for processing"""
        if not content or len(content.strip()) < 100:
            return False
        return True

class WebPageProcessor(ContentProcessor):
    """Processes web pages and articles"""
    
    def can_process(self, content_item: ContentItem) -> bool:
        return content_item.content_type in [ContentType.WEBPAGE, ContentType.ARTICLE]
    
    def process(self, content_item: ContentItem) -> ProcessedContent:
        """Extract and process web page content"""
        self.logger.info(f"Processing webpage: {content_item.source_url}")
        
        try:
            # Extract content from URL
            content_text = self._extract_web_content(content_item.source_url)
            
            if not self.validate_content(content_text):
                raise ValueError("Insufficient content extracted from webpage")
            
            # Create transcript-style format
            transcript = self._format_as_transcript(content_text, content_item)
            
            return ProcessedContent(
                content_id=content_item.content_id,
                original_type=content_item.content_type,
                title=content_item.title,
                transcript=transcript,
                attribution={
                    "source_type": "webpage",
                    "source_url": content_item.source_url,
                    "author": content_item.author,
                    "published_date": content_item.published_date.isoformat() if content_item.published_date else None
                },
                metadata={
                    "word_count": len(transcript.split()),
                    "extraction_method": "web_scraping",
                    "content_type": content_item.content_type.value
                },
                quality_score=self._assess_content_quality(content_text),
                processing_timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Failed to process webpage {content_item.source_url}: {str(e)}")
            raise
    
    def _extract_web_content(self, url: str) -> str:
        """Extract main content from web page"""
        try:
            # Try using newspaper3k for better content extraction
            try:
                from newspaper import Article
                
                article = Article(url)
                article.download()
                article.parse()
                
                content = f"Title: {article.title}\n\n"
                if article.authors:
                    content += f"Author(s): {', '.join(article.authors)}\n\n"
                content += article.text
                
                return content
                
            except ImportError:
                self.logger.warning("newspaper3k not available, using basic requests")
                
                # Fallback to basic requests + BeautifulSoup
                import requests
                from bs4 import BeautifulSoup
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Extract text content
                text = soup.get_text()
                
                # Clean up whitespace
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = ' '.join(chunk for chunk in chunks if chunk)
                
                return text
                
        except Exception as e:
            self.logger.error(f"Failed to extract content from {url}: {str(e)}")
            raise
    
    def _format_as_transcript(self, content: str, content_item: ContentItem) -> str:
        """Format web content as transcript-style text"""
        transcript = f"CONTENT TRANSCRIPT\n"
        transcript += f"Source: {content_item.source_url}\n"
        transcript += f"Type: {content_item.content_type.value}\n"
        transcript += f"Title: {content_item.title}\n"
        if content_item.author:
            transcript += f"Author: {content_item.author}\n"
        transcript += f"Processed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        transcript += "CONTENT:\n"
        transcript += content
        
        return transcript
    
    def _assess_content_quality(self, content: str) -> float:
        """Assess content quality for investment education relevance"""
        quality_score = 5.0  # Base score
        
        # Check for investment-related keywords
        investment_keywords = [
            'invest', 'stock', 'market', 'portfolio', 'finance', 'money',
            'trading', 'economy', 'business', 'wealth', 'financial'
        ]
        
        content_lower = content.lower()
        keyword_matches = sum(1 for keyword in investment_keywords if keyword in content_lower)
        
        # Adjust score based on relevance
        if keyword_matches >= 5:
            quality_score += 2.0
        elif keyword_matches >= 3:
            quality_score += 1.0
        
        # Check content length (optimal range)
        word_count = len(content.split())
        if 500 <= word_count <= 3000:
            quality_score += 1.0
        elif word_count > 3000:
            quality_score += 0.5
        
        return min(quality_score, 10.0)

class YouTubeProcessor(ContentProcessor):
    """Processes YouTube videos by extracting transcripts"""
    
    def can_process(self, content_item: ContentItem) -> bool:
        return content_item.content_type == ContentType.YOUTUBE
    
    def process(self, content_item: ContentItem) -> ProcessedContent:
        """Extract transcript from YouTube video"""
        self.logger.info(f"Processing YouTube video: {content_item.source_url}")
        
        try:
            # Extract video ID from URL
            video_id = self._extract_video_id(content_item.source_url)
            
            # Get transcript
            transcript_text = self._get_youtube_transcript(video_id)
            
            if not self.validate_content(transcript_text):
                raise ValueError("No suitable transcript found for YouTube video")
            
            # Format as transcript
            transcript = self._format_youtube_transcript(transcript_text, content_item)
            
            return ProcessedContent(
                content_id=content_item.content_id,
                original_type=content_item.content_type,
                title=content_item.title,
                transcript=transcript,
                attribution={
                    "source_type": "youtube",
                    "source_url": content_item.source_url,
                    "video_id": video_id,
                    "channel": content_item.author
                },
                metadata={
                    "word_count": len(transcript.split()),
                    "extraction_method": "youtube_transcript",
                    "video_id": video_id
                },
                quality_score=self._assess_content_quality(transcript_text),
                processing_timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Failed to process YouTube video {content_item.source_url}: {str(e)}")
            raise
    
    def _extract_video_id(self, url: str) -> str:
        """Extract YouTube video ID from URL"""
        import re
        
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
            r'youtube\.com/watch\?.*v=([^&\n?#]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        raise ValueError(f"Could not extract video ID from URL: {url}")
    
    def _get_youtube_transcript(self, video_id: str) -> str:
        """Get transcript from YouTube video"""
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            
            # Try to get transcript
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            
            # Combine transcript segments
            transcript_text = ' '.join([item['text'] for item in transcript_list])
            
            return transcript_text
            
        except ImportError:
            self.logger.error("youtube_transcript_api not available")
            raise ValueError("YouTube transcript extraction requires youtube_transcript_api package")
        except Exception as e:
            self.logger.error(f"Failed to get YouTube transcript: {str(e)}")
            raise
    
    def _format_youtube_transcript(self, transcript_text: str, content_item: ContentItem) -> str:
        """Format YouTube transcript"""
        transcript = f"YOUTUBE VIDEO TRANSCRIPT\n"
        transcript += f"Source: {content_item.source_url}\n"
        transcript += f"Title: {content_item.title}\n"
        if content_item.author:
            transcript += f"Channel: {content_item.author}\n"
        transcript += f"Processed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        transcript += "TRANSCRIPT:\n"
        transcript += transcript_text
        
        return transcript

class EbookProcessor(ContentProcessor):
    """Processes ebooks (PDF, EPUB)"""
    
    def can_process(self, content_item: ContentItem) -> bool:
        return content_item.content_type == ContentType.EBOOK
    
    def process(self, content_item: ContentItem) -> ProcessedContent:
        """Extract text from ebook"""
        self.logger.info(f"Processing ebook: {content_item.source_url}")
        
        try:
            # Download and extract text from ebook
            text_content = self._extract_ebook_text(content_item.source_url)
            
            if not self.validate_content(text_content):
                raise ValueError("Insufficient content extracted from ebook")
            
            # Limit content size for processing
            if len(text_content) > 50000:  # Limit to ~50k characters
                text_content = text_content[:50000] + "... [Content truncated for processing]"
            
            # Format as transcript
            transcript = self._format_ebook_transcript(text_content, content_item)
            
            return ProcessedContent(
                content_id=content_item.content_id,
                original_type=content_item.content_type,
                title=content_item.title,
                transcript=transcript,
                attribution={
                    "source_type": "ebook",
                    "source_url": content_item.source_url,
                    "author": content_item.author,
                    "format": self._detect_ebook_format(content_item.source_url)
                },
                metadata={
                    "word_count": len(transcript.split()),
                    "extraction_method": "ebook_parsing",
                    "content_truncated": len(text_content) >= 50000
                },
                quality_score=self._assess_content_quality(text_content),
                processing_timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Failed to process ebook {content_item.source_url}: {str(e)}")
            raise
    
    def _extract_ebook_text(self, url_or_path: str) -> str:
        """Extract text from ebook file"""
        try:
            # Determine if it's a URL or local path
            if url_or_path.startswith(('http://', 'https://')):
                # Download file first
                response = requests.get(url_or_path, timeout=60)
                response.raise_for_status()
                
                # Save to temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=self._get_file_extension(url_or_path)) as temp_file:
                    temp_file.write(response.content)
                    file_path = temp_file.name
            else:
                file_path = url_or_path
            
            # Extract text based on file type
            if file_path.lower().endswith('.pdf'):
                return self._extract_pdf_text(file_path)
            elif file_path.lower().endswith('.epub'):
                return self._extract_epub_text(file_path)
            else:
                raise ValueError(f"Unsupported ebook format: {file_path}")
                
        except Exception as e:
            self.logger.error(f"Failed to extract ebook text: {str(e)}")
            raise
    
    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            import PyPDF2
            
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            
            return text
            
        except ImportError:
            self.logger.error("PyPDF2 not available for PDF processing")
            raise ValueError("PDF processing requires PyPDF2 package")
        except Exception as e:
            self.logger.error(f"Failed to extract PDF text: {str(e)}")
            raise
    
    def _extract_epub_text(self, file_path: str) -> str:
        """Extract text from EPUB file"""
        try:
            import ebooklib
            from ebooklib import epub
            from bs4 import BeautifulSoup
            
            book = epub.read_epub(file_path)
            text = ""
            
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    text += soup.get_text() + "\n"
            
            return text
            
        except ImportError:
            self.logger.error("ebooklib not available for EPUB processing")
            raise ValueError("EPUB processing requires ebooklib package")
        except Exception as e:
            self.logger.error(f"Failed to extract EPUB text: {str(e)}")
            raise
    
    def _detect_ebook_format(self, url_or_path: str) -> str:
        """Detect ebook format from URL or path"""
        if url_or_path.lower().endswith('.pdf'):
            return 'PDF'
        elif url_or_path.lower().endswith('.epub'):
            return 'EPUB'
        else:
            return 'Unknown'
    
    def _get_file_extension(self, url: str) -> str:
        """Get file extension from URL"""
        from urllib.parse import urlparse
        path = urlparse(url).path
        return Path(path).suffix or '.pdf'  # Default to PDF
    
    def _format_ebook_transcript(self, text_content: str, content_item: ContentItem) -> str:
        """Format ebook content as transcript"""
        transcript = f"EBOOK CONTENT TRANSCRIPT\n"
        transcript += f"Source: {content_item.source_url}\n"
        transcript += f"Title: {content_item.title}\n"
        if content_item.author:
            transcript += f"Author: {content_item.author}\n"
        transcript += f"Format: {self._detect_ebook_format(content_item.source_url)}\n"
        transcript += f"Processed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        transcript += "CONTENT:\n"
        transcript += text_content
        
        return transcript

class NewsletterProcessor(ContentProcessor):
    """Processes newsletter content"""
    
    def can_process(self, content_item: ContentItem) -> bool:
        return content_item.content_type == ContentType.NEWSLETTER
    
    def process(self, content_item: ContentItem) -> ProcessedContent:
        """Process newsletter content"""
        self.logger.info(f"Processing newsletter: {content_item.title}")
        
        try:
            # Use raw content if provided, otherwise extract from URL
            if content_item.raw_content:
                content_text = content_item.raw_content
            else:
                content_text = self._extract_newsletter_content(content_item.source_url)
            
            if not self.validate_content(content_text):
                raise ValueError("Insufficient newsletter content")
            
            # Format as transcript
            transcript = self._format_newsletter_transcript(content_text, content_item)
            
            return ProcessedContent(
                content_id=content_item.content_id,
                original_type=content_item.content_type,
                title=content_item.title,
                transcript=transcript,
                attribution={
                    "source_type": "newsletter",
                    "source_url": content_item.source_url,
                    "author": content_item.author,
                    "published_date": content_item.published_date.isoformat() if content_item.published_date else None
                },
                metadata={
                    "word_count": len(transcript.split()),
                    "extraction_method": "newsletter_processing"
                },
                quality_score=self._assess_content_quality(content_text),
                processing_timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Failed to process newsletter {content_item.title}: {str(e)}")
            raise
    
    def _extract_newsletter_content(self, url: str) -> str:
        """Extract content from newsletter URL"""
        # This would be similar to web page extraction
        # but might need special handling for newsletter platforms
        web_processor = WebPageProcessor(self.config)
        return web_processor._extract_web_content(url)
    
    def _format_newsletter_transcript(self, content_text: str, content_item: ContentItem) -> str:
        """Format newsletter content as transcript"""
        transcript = f"NEWSLETTER CONTENT TRANSCRIPT\n"
        transcript += f"Source: {content_item.source_url}\n"
        transcript += f"Title: {content_item.title}\n"
        if content_item.author:
            transcript += f"Author: {content_item.author}\n"
        if content_item.published_date:
            transcript += f"Published: {content_item.published_date.strftime('%Y-%m-%d')}\n"
        transcript += f"Processed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        transcript += "CONTENT:\n"
        transcript += content_text
        
        return transcript

class PersonalPodcastProcessor(ContentProcessor):
    """Processes personal podcast episodes (MP3 files)"""
    
    def can_process(self, content_item: ContentItem) -> bool:
        return content_item.content_type == ContentType.PERSONAL_PODCAST
    
    def process(self, content_item: ContentItem) -> ProcessedContent:
        """Process personal podcast episode"""
        self.logger.info(f"Processing personal podcast: {content_item.title}")
        
        try:
            # Use existing podcast processing workflow
            from automation.podcast_harvester import PodcastHarvester
            
            # Create a temporary podcast item structure
            podcast_item = {
                'title': content_item.title,
                'url': content_item.source_url,
                'published': content_item.published_date or datetime.now(),
                'podcast_title': content_item.metadata.get('podcast_title', 'Personal Podcast') if content_item.metadata else 'Personal Podcast',
                'host_name': content_item.author or 'Unknown Host'
            }
            
            # Process using existing workflow
            harvester = PodcastHarvester(self.config)
            transcript_text = harvester.process_episode(podcast_item)
            
            if not self.validate_content(transcript_text):
                raise ValueError("Failed to generate transcript for personal podcast")
            
            return ProcessedContent(
                content_id=content_item.content_id,
                original_type=content_item.content_type,
                title=content_item.title,
                transcript=transcript_text,
                attribution={
                    "source_type": "personal_podcast",
                    "source_url": content_item.source_url,
                    "host": content_item.author,
                    "podcast_title": content_item.metadata.get('podcast_title') if content_item.metadata else None
                },
                metadata={
                    "word_count": len(transcript_text.split()),
                    "extraction_method": "audio_transcription"
                },
                quality_score=self._assess_content_quality(transcript_text),
                processing_timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Failed to process personal podcast {content_item.title}: {str(e)}")
            raise

class MultiContentProcessor:
    """Main processor that handles all content types"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.setup_logging()
        
        # Initialize all processors
        self.processors = [
            WebPageProcessor(config),
            YouTubeProcessor(config),
            EbookProcessor(config),
            NewsletterProcessor(config),
            PersonalPodcastProcessor(config)
        ]
        
        self.logger.info(f"MultiContentProcessor initialized with {len(self.processors)} processors")
    
    def setup_logging(self):
        """Setup logging"""
        self.logger = logging.getLogger(f"{__name__}.MultiContentProcessor")
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - MULTI-CONTENT - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def process_content_list(self, content_items: List[ContentItem]) -> List[ProcessedContent]:
        """Process a list of content items"""
        self.logger.info(f"Processing {len(content_items)} content items")
        
        processed_items = []
        
        for content_item in content_items:
            try:
                processed = self.process_single_item(content_item)
                processed_items.append(processed)
                self.logger.info(f"✅ Processed: {content_item.title[:50]}...")
                
            except Exception as e:
                self.logger.error(f"❌ Failed to process {content_item.title}: {str(e)}")
                continue
        
        self.logger.info(f"Successfully processed {len(processed_items)}/{len(content_items)} items")
        return processed_items
    
    def process_single_item(self, content_item: ContentItem) -> ProcessedContent:
        """Process a single content item"""
        # Find appropriate processor
        processor = self._find_processor(content_item)
        
        if not processor:
            raise ValueError(f"No processor available for content type: {content_item.content_type}")
        
        # Process the content
        return processor.process(content_item)
    
    def _find_processor(self, content_item: ContentItem) -> Optional[ContentProcessor]:
        """Find the appropriate processor for content type"""
        for processor in self.processors:
            if processor.can_process(content_item):
                return processor
        return None
    
    def get_supported_content_types(self) -> List[ContentType]:
        """Get list of supported content types"""
        supported_types = set()
        
        for processor in self.processors:
            # This is a simplified check - in practice, you'd query each processor
            if isinstance(processor, WebPageProcessor):
                supported_types.update([ContentType.WEBPAGE, ContentType.ARTICLE])
            elif isinstance(processor, YouTubeProcessor):
                supported_types.add(ContentType.YOUTUBE)
            elif isinstance(processor, EbookProcessor):
                supported_types.add(ContentType.EBOOK)
            elif isinstance(processor, NewsletterProcessor):
                supported_types.add(ContentType.NEWSLETTER)
            elif isinstance(processor, PersonalPodcastProcessor):
                supported_types.add(ContentType.PERSONAL_PODCAST)
        
        return list(supported_types)

def create_content_item(content_type: str, source_url: str, title: str, 
                       author: str = None, raw_content: str = None,
                       metadata: Dict[str, Any] = None) -> ContentItem:
    """Helper function to create ContentItem objects"""
    
    # Generate unique ID
    content_id = f"{content_type}_{int(time.time())}_{hash(source_url) % 10000}"
    
    return ContentItem(
        content_id=content_id,
        content_type=ContentType(content_type),
        source_url=source_url,
        title=title,
        author=author,
        published_date=datetime.now(),
        raw_content=raw_content,
        metadata=metadata or {}
    )

if __name__ == "__main__":
    # Test the multi-content processor
    print("🧪 Testing Multi-Content Processor")
    print("=" * 50)
    
    # Test configuration
    config = {
        'api_key': os.getenv('GEMINI_API_KEY', 'test_key'),
        'processing_limits': {
            'max_content_length': 50000,
            'timeout_seconds': 60
        }
    }
    
    try:
        processor = MultiContentProcessor(config)
        
        print(f"✅ Processor initialized successfully")
        print(f"📊 Supported content types: {[ct.value for ct in processor.get_supported_content_types()]}")
        
        # Test content item creation
        test_item = create_content_item(
            content_type="webpage",
            source_url="https://example.com/test-article",
            title="Test Investment Article",
            author="Test Author"
        )
        
        print(f"✅ Test content item created: {test_item.content_id}")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        traceback.print_exc()