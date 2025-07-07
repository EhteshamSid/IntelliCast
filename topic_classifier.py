from typing import Dict, List, Tuple, Any
import re
from settings import Config

class PoliticalClassifier:
    """Classifies whether a query is political or not"""
    
    POLITICAL_KEYWORDS = {
        'elections': ['election', 'vote', 'voting', 'ballot', 'campaign', 'candidate', 'primary', 'general election'],
        'government': ['congress', 'senate', 'house', 'president', 'governor', 'mayor', 'legislature', 'government'],
        'policies': ['policy', 'bill', 'law', 'legislation', 'act', 'regulation', 'executive order'],
        'parties': ['republican', 'democrat', 'democratic', 'gop', 'party', 'political party'],
        'issues': ['immigration', 'healthcare', 'economy', 'tax', 'budget', 'foreign policy', 'defense', 'debt ceiling'],
        'events': ['debate', 'rally', 'protest', 'hearing', 'committee', 'session', 'inauguration'],
        'officials': ['politician', 'representative', 'senator', 'congressman', 'congresswoman', 'official']
    }
    
    NON_POLITICAL_KEYWORDS = [
        'recipe', 'cooking', 'food', 'sports', 'entertainment', 'movie', 'music',
        'science', 'technology', 'health', 'medical', 'weather', 'travel', 'shopping',
        'fashion', 'beauty', 'gaming', 'video game', 'anime', 'manga', 'fiction'
    ]
    
    def classify_query(self, query: str) -> Tuple[bool, float, str]:
        """
        Classify if a query is political
        Returns: (is_political, confidence, reasoning)
        """
        query_lower = query.lower()
        
        # Check for non-political keywords first
        for keyword in self.NON_POLITICAL_KEYWORDS:
            if keyword in query_lower:
                return False, 0.9, f"Query contains non-political keyword: {keyword}"
        
        # Count political keywords
        political_score = 0
        matched_categories = []
        
        for category, keywords in self.POLITICAL_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query_lower:
                    political_score += 1
                    if category not in matched_categories:
                        matched_categories.append(category)
        
        # Calculate confidence based on keyword matches
        confidence = min(political_score / 3.0, 1.0)  # Normalize to 0-1
        
        # Determine if political
        is_political = political_score >= 1
        
        reasoning = f"Found {political_score} political keywords in categories: {', '.join(matched_categories)}"
        
        return is_political, confidence, reasoning

class BiasDetector:
    """Detects bias in responses"""
    
    def __init__(self):
        self.bias_keywords = Config.BIAS_KEYWORDS
        
    def detect_bias(self, text: str) -> Dict[str, Any]:
        """
        Detect bias in text
        Returns: Dictionary with bias analysis
        """
        text_lower = text.lower()
        bias_analysis = {
            'has_bias': False,
            'bias_types': [],
            'biased_phrases': [],
            'confidence': 0.0
        }
        
        total_issues = 0
        
        # Check for partisan language
        for keyword in self.bias_keywords['partisan']:
            if keyword in text_lower:
                bias_analysis['bias_types'].append('partisan')
                bias_analysis['biased_phrases'].append(keyword)
                total_issues += 1
        
        # Check for emotional language
        for keyword in self.bias_keywords['emotional']:
            if keyword in text_lower:
                bias_analysis['bias_types'].append('emotional')
                bias_analysis['biased_phrases'].append(keyword)
                total_issues += 1
        
        # Check for absolute statements
        for keyword in self.bias_keywords['absolute']:
            if keyword in text_lower:
                bias_analysis['bias_types'].append('absolute')
                bias_analysis['biased_phrases'].append(keyword)
                total_issues += 1
        
        # Check for one-sided perspective
        republican_indicators = ['republican', 'gop', 'conservative', 'right-wing']
        democratic_indicators = ['democrat', 'democratic', 'liberal', 'left-wing']
        
        republican_count = sum(1 for indicator in republican_indicators if indicator in text_lower)
        democratic_count = sum(1 for indicator in democratic_indicators if indicator in text_lower)
        
        if republican_count > 0 and democratic_count == 0:
            bias_analysis['bias_types'].append('one_sided_republican')
            total_issues += 2
        elif democratic_count > 0 and republican_count == 0:
            bias_analysis['bias_types'].append('one_sided_democratic')
            total_issues += 2
        
        # Determine if biased
        bias_analysis['has_bias'] = total_issues > 0
        bias_analysis['confidence'] = min(total_issues / 5.0, 1.0)  # Normalize to 0-1
        
        return bias_analysis
    
    def suggest_corrections(self, bias_analysis: Dict[str, Any]) -> List[str]:
        """Suggest corrections for detected bias"""
        suggestions = []
        
        if 'partisan' in bias_analysis['bias_types']:
            suggestions.append("Replace partisan language with neutral terms")
        
        if 'emotional' in bias_analysis['bias_types']:
            suggestions.append("Use objective language instead of emotional terms")
        
        if 'absolute' in bias_analysis['bias_types']:
            suggestions.append("Qualify absolute statements with appropriate context")
        
        if 'one_sided_republican' in bias_analysis['bias_types']:
            suggestions.append("Include Democratic perspective to balance the response")
        
        if 'one_sided_democratic' in bias_analysis['bias_types']:
            suggestions.append("Include Republican perspective to balance the response")
        
        return suggestions

class CitationChecker:
    """Checks for proper citations in responses"""
    
    def check_citations(self, text: str) -> Dict[str, Any]:
        """
        Check if response has proper citations
        Returns: Dictionary with citation analysis
        """
        citation_analysis = {
            'has_citations': False,
            'citation_count': 0,
            'citation_sources': [],
            'missing_citations': [],
            'confidence': 0.0
        }
        
        # Look for citation patterns
        citation_patterns = [
            r'\[([^\]]+)\]',  # [source]
            r'\(([^)]+)\)',   # (source)
            r'according to ([^,\.]+)',  # according to source
            r'as reported by ([^,\.]+)',  # as reported by source
            r'source: ([^,\.]+)',  # source: name
        ]
        
        for pattern in citation_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            citation_analysis['citation_count'] += len(matches)
            citation_analysis['citation_sources'].extend(matches)
        
        # Check for factual claims that need citations
        factual_indicators = [
            'reported', 'announced', 'stated', 'said', 'confirmed', 'revealed',
            'passed', 'voted', 'elected', 'appointed', 'signed', 'enacted'
        ]
        
        sentences = text.split('.')
        for sentence in sentences:
            sentence_lower = sentence.lower()
            has_factual_claim = any(indicator in sentence_lower for indicator in factual_indicators)
            has_citation = any(pattern in sentence for pattern in citation_patterns)
            
            if has_factual_claim and not has_citation:
                citation_analysis['missing_citations'].append(sentence.strip())
        
        citation_analysis['has_citations'] = citation_analysis['citation_count'] > 0
        citation_analysis['confidence'] = min(citation_analysis['citation_count'] / 3.0, 1.0)
        
        return citation_analysis 