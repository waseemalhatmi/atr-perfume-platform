
import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageSquare, Send, X, Sparkles, User, Bot, ExternalLink } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import { fetchItem, imageUrl } from '../lib/api';
import { logger } from '@/lib/logger';
import '../styles/chat.css';

interface Message {
  id: string;
  text: string;
  sender: 'bot' | 'user';
  timestamp: Date;
  productIds?: number[];
}

const QUICK_ACTIONS = [
  "اقترح لي عطر هدية",
  "ما هي العطور المشابهة لـ ديور ساواج؟",
  "أبحث عن عطر بارد للصيف",
  "كيف أختار عطري المفضل؟"
];

const ProductSnippet: React.FC<{ id: number }> = ({ id }) => {
  const [item, setItem] = useState<any>(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchItem(id)
      .then(data => {
        if (data && data.item) setItem(data.item);
      })
      .catch(err => logger.error("Snippet Fetch Error:", err));
  }, [id]);

  if (!item) return null;

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="product-mini-card"
      onClick={() => navigate(`/items/${item.id}`)}
    >
      <img 
        src={item.images && item.images[0] ? imageUrl(item.images[0].path) : '/placeholder.jpg'} 
        alt={item.name} 
        className="product-mini-img" 
      />
      <div className="product-mini-info">
        <h4 className="product-mini-name">{item.name}</h4>
        <p className="product-mini-brand">{item.brand.name}</p>
        <span className="product-mini-price">{item.min_price} {item.currency}</span>
      </div>
      <ExternalLink size={14} className="product-mini-icon" />
    </motion.div>
  );
};

const ChatAssistant: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: 'مرحباً بك! أنا مساعدك العطري الشخصي. كيف يمكنني مساعدتك في اكتشاف عطر يمثل شخصيتك اليوم؟',
      sender: 'bot',
      timestamp: new Date()
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const navigate = useNavigate();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSend = async (text: string = inputValue) => {
    if (!text.trim() || isTyping) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      text,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMsg]);
    setInputValue('');
    setIsTyping(true);

    const botMsgId = (Date.now() + 1).toString();
    // Placeholder for streaming message
    setMessages(prev => [...prev, {
      id: botMsgId,
      text: '',
      sender: 'bot',
      timestamp: new Date()
    }]);

    try {
      const history = messages.map(m => ({
        role: m.sender === 'bot' ? 'model' : 'user',
        parts: [{ text: m.text }]
      }));

      const response = await fetch('/api/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, history, stream: true })
      });

      if (!response.body) throw new Error("No response body");
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulatedText = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        accumulatedText += decoder.decode(value, { stream: true });
        
        setMessages(prev => prev.map(m => 
          m.id === botMsgId ? { ...m, text: accumulatedText } : m
        ));
      }

      // After streaming is done, parse for product IDs
      const productIds = Array.from(accumulatedText.matchAll(/\[PRODUCT:(\d+)\]/g))
        .map(match => parseInt(match[1]));
      
      if (productIds.length > 0) {
        setMessages(prev => prev.map(m => 
          m.id === botMsgId ? { ...m, productIds } : m
        ));
      }

    } catch (error) {
      logger.error("Chat Error:", error);
      setMessages(prev => prev.map(m => 
        m.id === botMsgId ? { ...m, text: 'عذراً، واجهت مشكلة في الاتصال بخبير العطور. يرجى المحاولة لاحقاً.' } : m
      ));
    } finally {
      setIsTyping(false);
      setTimeout(() => {
        if (inputRef.current) inputRef.current.focus();
      }, 100);
    }
  };

  const renderMessageText = (text: string) => {
    // Remove [PRODUCT:ID] tags from visible text before rendering markdown
    const cleanedText = text.replace(/\[PRODUCT:\d+\]/g, '').trim();
    return (
      <div className="markdown-content">
        <ReactMarkdown>{cleanedText}</ReactMarkdown>
      </div>
    );
  };

  return (
    <div className="chat-container">
      <motion.div 
        className="chat-bubble"
        onClick={() => setIsOpen(!isOpen)}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
      >
        {isOpen ? <X /> : <MessageSquare />}
        {!isOpen && <span className="bubble-ping" />}
      </motion.div>

      <AnimatePresence>
        {isOpen && (
          <motion.div 
            className="chat-window"
            initial={{ opacity: 0, scale: 0.8, y: 50, x: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0, x: 0 }}
            exit={{ opacity: 0, scale: 0.8, y: 50, x: 20 }}
          >
            <div className="chat-header">
              <div className="chat-header-info">
                <div className="chat-avatar">
                  <Sparkles size={18} color="white" />
                </div>
                <div>
                  <h3 className="chat-title">الخبير العطري</h3>
                  <div className="status-container">
                    <span className="status-dot" />
                    <span className="chat-status">نشط الآن للخدمة</span>
                  </div>
                </div>
              </div>
              <button onClick={() => setIsOpen(false)} className="close-btn">
                <X size={20} />
              </button>
            </div>

            <div className="chat-body">
              {messages.map((msg) => (
                <div key={msg.id} className="message-wrapper">
                  <div className={`message ${msg.sender}`}>
                    {renderMessageText(msg.text)}
                    {msg.sender === 'bot' && msg.text === '' && (
                      <div className="typing-dots">
                        <span>.</span><span>.</span><span>.</span>
                      </div>
                    )}
                  </div>
                  {msg.productIds && msg.productIds.length > 0 && (
                    <div className="chat-products-list">
                      {msg.productIds.map(pid => (
                        <ProductSnippet key={pid} id={pid} />
                      ))}
                    </div>
                  )}
                </div>
              ))}
              
              {!isTyping && messages.length === 1 && (
                <div className="quick-actions-container">
                  <p className="quick-actions-hint">أمثلة لأسئلة يمكنك طرحها:</p>
                  <div className="quick-actions-grid">
                    {QUICK_ACTIONS.map((action, i) => (
                      <button key={i} onClick={() => handleSend(action)} className="quick-action-btn">
                        {action}
                      </button>
                    ))}
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            <div className="chat-footer">
              <div className="input-wrapper">
                <textarea 
                  ref={inputRef}
                  className="chat-input" 
                  placeholder="ابحث عن عطرك المفضل... (Shift+Enter لسطر جديد)"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSend();
                    }
                  }}
                  rows={1}
                  style={{ resize: 'none', paddingRight: '3.5rem' }}
                />
                <button 
                  type="button" 
                  aria-label="إرسال"
                  disabled={isTyping || !inputValue.trim()}
                  className={`send-btn ${inputValue.trim() ? 'active' : ''}`} 
                  onClick={() => handleSend()}
                >
                  <Send size={18} />
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ChatAssistant;
