/**
 * EXPIRYGUARD AI — MULTILINGUAL STORE ASSISTANT CHATBOT
 * Fully functional conversational AI with real-time inventory query & speech synthesis
 */

let isChatOpen = false;
let isAudioEnabled = true;
let chatRequestPending = false;

function toggleChatbot() {
  const windowElem = document.getElementById('chatbot-window');
  if (!windowElem) return;

  isChatOpen = !isChatOpen;
  if (isChatOpen) {
    windowElem.classList.add('active');
    document.getElementById('chatbot-user-input').focus();
    // Greet if messages container is empty
    const msgContainer = document.getElementById('chatbot-messages');
    if (msgContainer.children.length === 0) {
      sendChatbotQuery("hello", false);
    }
  } else {
    windowElem.classList.remove('active');
  }
}

async function sendChatbotQuery(queryText, displayUserBubble = true) {
  const text = queryText.trim();
  if (!text || chatRequestPending) return;

  const msgContainer = document.getElementById('chatbot-messages');
  const inputElem = document.getElementById('chatbot-user-input');

  if (displayUserBubble) {
    const userBubble = document.createElement('div');
    userBubble.className = 'chat-bubble chat-bubble-user';
    userBubble.textContent = text;
    msgContainer.appendChild(userBubble);
    inputElem.value = "";
    msgContainer.scrollTop = msgContainer.scrollHeight;
  }

  chatRequestPending = true;
  const sendBtn = document.getElementById('chatbot-send-btn');
  if (sendBtn) sendBtn.disabled = true;

  // Temporary typing indicator
  const typingBubble = document.createElement('div');
  typingBubble.className = 'chat-bubble chat-bubble-bot';
  typingBubble.innerHTML = '<span style="font-size:0.8rem; color:#6b7280;">Thinking... 💭</span>';
  msgContainer.appendChild(typingBubble);
  msgContainer.scrollTop = msgContainer.scrollHeight;

  const currentLang = document.documentElement.lang || 'en';

  try {
    const res = await fetch('/api/chatbot/message', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, lang: currentLang })
    });
    const data = await res.json();
    typingBubble.remove();

    const botBubble = document.createElement('div');
    botBubble.className = 'chat-bubble chat-bubble-bot';

    const source = document.createElement('small');
    source.className = 'chat-response-source';
    source.textContent = data.mode === 'ai' ? 'AI · using live store data' : 'Database fallback · live store data';
    const reply = document.createElement('div');
    reply.className = 'chat-response-text';
    reply.textContent = data.reply || 'No reply was returned.';
    botBubble.append(source, reply);
    msgContainer.appendChild(botBubble);
    msgContainer.scrollTop = msgContainer.scrollHeight;

    // Speak aloud if audio enabled
    if (isAudioEnabled && displayUserBubble) {
      speakBotReply(data.reply || '', currentLang);
    }

  } catch (err) {
    typingBubble.remove();
    const errorBubble = document.createElement('div');
    errorBubble.className = 'chat-bubble chat-bubble-bot';
    errorBubble.textContent = "I couldn't reach the chatbot service. Please check the connection and try again.";
    msgContainer.appendChild(errorBubble);
  } finally {
    chatRequestPending = false;
    if (sendBtn) sendBtn.disabled = false;
  }
}

function speakBotReply(textHtml, lang) {
  if (!('speechSynthesis' in window)) return;

  // Clean html tags for clean audio speech
  const cleanText = textHtml.replace(/<[^>]*>?/gm, ' ');
  window.speechSynthesis.cancel(); // Stop any previous speech

  const utterance = new SpeechSynthesisUtterance(cleanText);
  if (lang === 'hi') utterance.lang = 'hi-IN';
  else if (lang === 'mr') utterance.lang = 'mr-IN';
  else utterance.lang = 'en-IN';

  utterance.rate = 1.0;
  window.speechSynthesis.speak(utterance);
}

function toggleAudioMute() {
  isAudioEnabled = !isAudioEnabled;
  const btn = document.getElementById('chatbot-audio-toggle');
  if (btn) {
    btn.textContent = isAudioEnabled ? '🔊' : '🔇';
    btn.title = isAudioEnabled ? 'Voice Enabled' : 'Voice Muted';
  }
  if (!isAudioEnabled && 'speechSynthesis' in window) {
    window.speechSynthesis.cancel();
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const launcher = document.getElementById('chatbot-launcher-btn');
  if (launcher) launcher.addEventListener('click', toggleChatbot);

  const closeBtn = document.getElementById('chatbot-close-btn');
  if (closeBtn) closeBtn.addEventListener('click', toggleChatbot);

  const sendBtn = document.getElementById('chatbot-send-btn');
  const input = document.getElementById('chatbot-user-input');

  if (sendBtn && input) {
    sendBtn.addEventListener('click', () => sendChatbotQuery(input.value, true));
    input.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') sendChatbotQuery(input.value, true);
    });
  }

  const audioToggle = document.getElementById('chatbot-audio-toggle');
  if (audioToggle) audioToggle.addEventListener('click', toggleAudioMute);
});
