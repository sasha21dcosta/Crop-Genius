from django.db import models
from django.contrib.auth.models import User
import json

class ChatSession(models.Model):
    """Stores a disease diagnosis chat session"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='diagnosis_chats')
    crop = models.CharField(max_length=50)  # rice, wheat, apple, etc.
    title = models.CharField(max_length=200, blank=True)  # Auto-generated or user-provided
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)  # To soft-delete or archive
    
    class Meta:
        ordering = ['-updated_at']  # Most recent first
        indexes = [
            models.Index(fields=['user', '-updated_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.crop} - {self.title or 'Untitled'}"
    
    def get_preview(self):
        """Get first user message as preview"""
        first_msg = self.messages.filter(is_user=True).first()
        if first_msg:
            return first_msg.text[:50] + ('...' if len(first_msg.text) > 50 else '')
        return "New conversation"

class ChatMessage(models.Model):
    """Individual messages within a chat session"""
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    text = models.TextField()
    is_user = models.BooleanField()  # True = user message, False = AI response
    metadata = models.JSONField(null=True, blank=True)  # Store disease info, confidence, etc.
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']  # Chronological order
    
    def __str__(self):
        sender = "User" if self.is_user else "AI"
        return f"{sender}: {self.text[:30]}..."
