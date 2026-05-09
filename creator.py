import json
import logging
import re
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class ContentCreator:
    """
    AI Agent logic migrated from n8n workflow for generating social media posts.
    Supports OpenAI, Gemini, and OpenRouter.
    """
    
    def __init__(
        self, 
        model_name: str = "gpt-4o-mini", 
        api_key: Optional[str] = None, 
        provider: str = "openai", 
        google_api_key: Optional[str] = None,
        openrouter_api_key: Optional[str] = None
    ):
        self.provider = provider.lower()
        self.model_name = model_name
        self.api_key = api_key
        self.google_api_key = google_api_key
        self.openrouter_api_key = openrouter_api_key
        self.client = None
        self.genai = None

        if self.provider == "openai":
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=api_key)
            except ImportError:
                logger.warning("openai package not installed.")
        elif self.provider == "openrouter":
            try:
                from openai import OpenAI
                self.client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=openrouter_api_key
                )
            except ImportError:
                logger.warning("openai package not installed (required for OpenRouter).")
        elif self.provider == "gemini":
            try:
                import google.generativeai as genai
                genai.configure(api_key=google_api_key)
                self.genai = genai
                # Map gpt-4o-mini to gemini-1.5-flash if not specified
                if "gpt" in self.model_name:
                    self.model_name = "gemini-1.5-flash"
            except ImportError:
                logger.warning("google-generativeai package not installed.")

    def create_image_post(
        self, 
        platform: str, 
        old_title: str, 
        old_caption: str, 
        old_hashtags: str
    ) -> Optional[Dict[str, str]]:
        """
        Generates content for an image post based on the platform.
        """
        length_target = self._get_image_length_target(platform)
        
        prompt = f"""You are an Indian Eco-Friendly & Sustainable Packaging Manufacturer and Exporter supplying packaging solutions to international buyers, importers, distributors, wholesalers, and brands across global markets, including South Africa. Your content must reflect manufacturing expertise, sustainability compliance, export readiness, and buyer awareness — without branding or promotion.

TASK:
Rewrite the title, caption, AND hashtags for a sustainable packaging manufacturing and exporting business. Preserve the original intent and context of the inputs without copying word-to-word. The purpose is to build trust through clarity, experience, sustainability knowledge, and export understanding.

INPUTS:
Old Title: "{old_title}"
Old Caption: "{old_caption}"
Old Hashtags: "{old_hashtags}"

CONTENT RULES:

Language: English only

Tone: Professional, human, manufacturer-focused

Perspective: Sustainable packaging manufacturer & exporter (NOT coach, NOT consultant)

Audience: Global packaging buyers, sourcing teams, and procurement managers

Short, punchy sentences

Do NOT change the original meaning

Do NOT copy old content word-to-word

Do NOT add any CTA

Do NOT mention any company name, brand name, factory name, person name, website, email, phone number, or link

Do NOT include URLs, domains, or social handles

Title must be short, hook-driven, curiosity-based

Caption must be emotional + practical + packaging export-specific

Mention real buyer-side pains (inconsistent quality, sustainability claims vs reality, price pressure, compliance confusion, MOQ issues, delivery delays, trust gaps)

Include at least one practical manufacturing, material, or export insight (certifications, recyclability, food-grade, durability, supply chain consistency)

{platform} caption length target: ~{length_target} characters

HASHTAG RULES:

Generate 4 generic, non-branded hashtags

Hashtags must support global reach

Focus on sustainable packaging, eco-friendly manufacturing, export supply chains, OEM/ODM, private label packaging

Avoid brand names, company names, locations, or local-only tags

Do NOT repeat hashtags

FORMATTING RULES (VERY IMPORTANT):
• Do NOT use real line breaks
• Use <<LB>> wherever a line break should appear
• Preserve spacing exactly using <<LB>>
• Caption MUST include intentional line breaks
• Structure the caption in this exact flow:

LINE 1–2:
Short emotional hook (1 line each, max 6–7 words)

<<LB>>

LINE 3–6:
2–4 short punchy lines
Each line on a new line
Packaging export reality or buyer concern

<<LB>>

PARAGRAPH BLOCK:
One compact paragraph (3–4 lines max)
Practical manufacturing, sustainability, or export insight
Factory-experienced tone

<<LB>>

CLOSING LINES:
2 short lines
Trust, consistency, sustainability, or capability positioning

• Do NOT remove line breaks
• Do NOT convert into a single paragraph
• Keep spacing exactly as written
• Line breaks must remain visible in final output

OUTPUT FORMAT (STRICT):
Return ONLY raw JSON
No explanation
No markdown
No extra text

CRITICAL OUTPUT RULE:
Return JSON in ONE SINGLE LINE
Do NOT use \\n
Do NOT use actual newlines
Use <<LB>> only
All values must be plain text strings

OUTPUT SANITIZATION RULE (CRITICAL):
Do NOT use \\n or any escaped newline characters
Output must be a single continuous line
Only allowed line break marker is <<LB>>
JSON must begin with {{ and end with }} on the same line

FINAL OUTPUT FORMAT (EXACT):
{{
"title": TITLE_TEXT_HERE,
"caption": CAPTION_TEXT_HERE,
"hashtags": HASHTAGS_TEXT_HERE
}}

IMPORTANT:
• Do NOT use quotation marks inside title, caption, or hashtags values
• Do NOT break JSON structure
• Ensure caption is complete and not cut off
• Finish all sentences cleanly
• Do NOT include any external links, company names, or copyrighted references"""

        raw_response = self._call_llm(prompt)
        if not raw_response:
            return None
            
        parsed = self._parse_llm_output(raw_response)
        
        caption = parsed.get("caption", "")
        title = parsed.get("title", "")
        
        if old_hashtags:
            caption += f"\n{old_hashtags}"
            
        return {
            "title": title,
            "caption": caption
        }

    def create_video_post(
        self, 
        platform: str, 
        old_title: str, 
        old_caption: str,
        old_hashtags: str
    ) -> Optional[Dict[str, str]]:
        """
        Generates content for a video post based on the platform.
        """
        post_type = self._get_video_post_type(platform)
        length_target = self._get_video_length_target(platform)
        
        prompt = f"""Create a unique and engaging social media {post_type} post about Zilokraft, an end-to-end packaging solutions company, with a strong, attention-grabbing title and an engaging caption that promotes a product, service, or idea while establishing credibility and sparking discussion. The tone should be insightful, informative, and inspiring, making it valuable for Instagram’s professional audience.

Key Elements to Include:
✅ A powerful title that draws interest and sets the stage for the post.
✅ An engaging opening hook that immediately captures attention.
✅ Storytelling or industry insights (e.g., how Zilokraft’s solutions solve packaging challenges, reduce waste, or align with sustainability trends).
✅ Clear benefits and unique value propositions to highlight why Zilokraft matters (e.g., innovation, sustainability, reliability, customization).
✅ A thought-provoking question or call to action to encourage comments and engagement (e.g., “What’s the biggest challenge you face in packaging?” “How do you see sustainable packaging shaping your industry?”).
✅ Professional yet conversational tone to keep it relatable.
✅ Relevant industry hashtags to boost visibility.

The caption should be within around {length_target} characters, ensuring a structured flow that maximizes readability and engagement. Do not include any links in the caption.

Old caption: {old_caption}
Old title: {old_title}

Output format (JSON enclosed in curly braces only):

{{
  "title": "PLACEHOLDER",
  "caption": "PLACEHOLDER"
}}"""

        raw_response = self._call_llm(prompt)
        if not raw_response:
            return None
            
        parsed = self._parse_llm_output(raw_response)
        
        caption = parsed.get("caption", "")
        title = parsed.get("title", "")
        
        if old_hashtags:
            caption += f"\n{old_hashtags}"
            
        return {
            "title": title,
            "caption": caption
        }

    def _get_image_length_target(self, platform: str) -> int:
        platform_lower = platform.lower()
        if platform_lower == "twitter":
            return 150
        return 350

    def _get_video_post_type(self, platform: str) -> str:
        platform_lower = platform.lower()
        if platform_lower == "instagram":
            return "Instagram Reel"
        elif platform_lower == "twitter":
            return "Twitter video"
        elif platform_lower == "linkedin":
            return "Linkedin Video"
        elif platform_lower == "pinterest":
            return "Pinterest Video"
        return f"{platform} Video"

    def _get_video_length_target(self, platform: str) -> int:
        platform_lower = platform.lower()
        if platform_lower == "twitter":
            return 250
        return 500

    def _call_llm(self, prompt: str) -> Optional[str]:
        try:
            if (self.provider == "openai" or self.provider == "openrouter") and self.client:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                )
                return response.choices[0].message.content.strip()
            elif self.provider == "gemini" and self.genai:
                model = self.genai.GenerativeModel(self.model_name)
                response = model.generate_content(prompt)
                return response.text.strip()
            else:
                logger.error(f"LLM Provider {self.provider} not configured or package missing.")
                return None
        except Exception as e:
            logger.error(f"Error calling LLM ({self.provider}): {e}")
            return None

    def _parse_llm_output(self, content: str) -> Dict[str, str]:
        """
        Parses the JSON output from the LLM, handling n8n specific formatting like <<LB>>.
        """
        clean_content = content.strip()
        if clean_content.startswith("```json"):
            clean_content = clean_content[7:]
        elif clean_content.startswith("```"):
            clean_content = clean_content[3:]
        if clean_content.endswith("```"):
            clean_content = clean_content[:-3]
            
        clean_content = clean_content.strip()

        try:
            parsed = json.loads(clean_content)
            if "caption" in parsed and isinstance(parsed["caption"], str):
                parsed["caption"] = parsed["caption"].replace("<<LB>>", "\n")
            return parsed
        except json.JSONDecodeError:
            logger.warning("JSON Decode Error, falling back to regex parsing")
            title = ""
            caption = ""
            
            title_match = re.search(r'"title"\s*:\s*(.+?)(?=\s*,\s*"caption")', clean_content)
            if title_match:
                t = title_match.group(1).strip()
                if t.startswith('"') and t.endswith('"'):
                    t = t[1:-1]
                title = t
                
            caption_match = re.search(r'"caption"\s*:\s*([\s\S]*?)\n?\s*}', clean_content)
            if caption_match:
                c = caption_match.group(1).strip()
                if c.startswith('"') and c.endswith('"'):
                    c = c[1:-1]
                caption = c.replace("<<LB>>", "\n")
                
            return {
                "title": title,
                "caption": caption
            }
