import "./App.css";
import { useState, useEffect, useRef } from "react";
import {
  Sparkles,
  Plus,
  MessageSquare,
  Settings,
  User,
  Mic,
  Paperclip,
  ArrowUp,
  Image,
  FileText,
  Wand2,
  Lightbulb,
  X,
  Home,
  User as UserIcon,
  Palette,
  Bell,
  AudioWaveform,
  Code,
  Video,
  File,
} from "lucide-react";

export default function App() {
  // ===== STATE =====
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [activeSettingsTab, setActiveSettingsTab] = useState("General");
  const [isUploadPanelOpen, setIsUploadPanelOpen] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [filePreview, setFilePreview] = useState(null);

  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);
  const fileInputRef = useRef(null);

  // ===== EFFECTS =====
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // ===== SPEECH RECOGNITION (auto‑detect) =====
  const startListening = () => {
    if (!("webkitSpeechRecognition" in window) && !("SpeechRecognition" in window)) {
      alert("Speech recognition is not supported in your browser.");
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = ""; // auto‑detect
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => {
      setIsListening(true);
    };

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setInput((prev) => prev + (prev ? " " : "") + transcript);
      setIsListening(false);
    };

    recognition.onerror = () => {
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.start();
    recognitionRef.current = recognition;
  };

  const stopListening = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    setIsListening(false);
  };

  const toggleListening = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };

  // ===== FILE UPLOAD HANDLING =====
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploadedFile(file);

    if (file.type.startsWith("image/")) {
      const reader = new FileReader();
      reader.onload = (event) => {
        setFilePreview(event.target.result);
      };
      reader.readAsDataURL(file);
    } else {
      setFilePreview(null);
    }
  };

  const clearFile = () => {
    setUploadedFile(null);
    setFilePreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  // ===== HANDLERS =====
  const handleSend = () => {
    const text = input.trim();
    if (!text && !uploadedFile) return;

    let userMessageText = text || "";
    let fileData = null;
    if (uploadedFile) {
      const fileInfo = uploadedFile.name;
      userMessageText += (text ? "\n" : "") + `📎 ${fileInfo}`;
      fileData = {
        name: uploadedFile.name,
        type: uploadedFile.type,
        dataURL: filePreview,
      };
    }

    const newMessage = {
      id: Date.now(),
      role: "user",
      text: userMessageText,
      file: fileData,
    };
    setMessages((prev) => [...prev, newMessage]);

    setInput("");
    clearFile();

    // Assistant response with typing effect
    const assistantId = Date.now() + 1;
    const fullResponse = "Please give me a moment.";
    setMessages((prev) => [...prev, { id: assistantId, role: "assistant", text: "" }]);

    let index = 0;
    const interval = setInterval(() => {
      if (index < fullResponse.length) {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantId
              ? { ...msg, text: fullResponse.substring(0, index + 1) }
              : msg
          )
        );
        index++;
      } else {
        clearInterval(interval);
      }
    }, 10);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleSend();
    }
  };

  const handlePillClick = (text) => {
    setInput(text);
  };

  const handleGenClick = (type) => {
    // Create a mock file based on the generation type
    let mockFile = null;
    switch(type) {
      case "Audio":
        mockFile = { name: "generated_audio.mp3", type: "audio/mpeg", dataURL: null };
        break;
      case "Image": {
        // Generate a placeholder gradient image
        const canvas = document.createElement("canvas");
        canvas.width = 100;
        canvas.height = 100;
        const ctx = canvas.getContext("2d");
        const gradient = ctx.createLinearGradient(0, 0, 100, 100);
        gradient.addColorStop(0, "#ff6b6b");
        gradient.addColorStop(1, "#4ecdc4");
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, 100, 100);
        const dataURL = canvas.toDataURL("image/png");
        mockFile = { name: "generated_image.png", type: "image/png", dataURL };
        break;
      }
      case "Code":
        mockFile = { name: "generated_code.py", type: "text/x-python", dataURL: null };
        break;
      case "Video":
        mockFile = { name: "generated_video.mp4", type: "video/mp4", dataURL: null };
        break;
      default:
        return;
    }

    const userMsg = {
      id: Date.now(),
      role: "user",
      text: `Generate ${type}`,
      file: mockFile,
    };
    setMessages((prev) => [...prev, userMsg]);

    // Assistant with typing effect
    const assistantId = Date.now() + 1;
    const fullResponse = `I'm generating your ${type}. It will be ready soon.`;
    setMessages((prev) => [...prev, { id: assistantId, role: "assistant", text: "" }]);

    let index = 0;
    const interval = setInterval(() => {
      if (index < fullResponse.length) {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantId
              ? { ...msg, text: fullResponse.substring(0, index + 1) }
              : msg
          )
        );
        index++;
      } else {
        clearInterval(interval);
      }
    }, 10);

    setIsUploadPanelOpen(false);
  };

  const resetChat = () => {
    setMessages([]);
    setInput("");
    clearFile();
  };

  const deleteMessage = (id) => {
    setMessages((prev) => prev.filter((msg) => msg.id !== id));
  };

  // ===== SETTINGS TABS =====
  const settingsTabs = [
    { id: "General", icon: Home },
    { id: "Account", icon: UserIcon },
    { id: "Appearance", icon: Palette },
    { id: "Notifications", icon: Bell },
  ];

  // ===== RENDER =====
  const isChatEmpty = messages.length === 0;

  return (
    <div className="app-container">
      {/* ===== SETTINGS MODAL ===== */}
      {isSettingsOpen && (
        <div
          className="settings-overlay"
          onClick={() => setIsSettingsOpen(false)}
        >
          <div
            className="settings-modal"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="settings-sidebar">
              <div className="settings-sidebar-header">
                <Settings size={20} />
                <h2>Settings</h2>
              </div>
              {settingsTabs.map((tab) => (
                <button
                  key={tab.id}
                  className={`settings-tab ${
                    activeSettingsTab === tab.id ? "active" : ""
                  }`}
                  onClick={() => setActiveSettingsTab(tab.id)}
                >
                  <tab.icon size={18} />
                  {tab.id}
                </button>
              ))}
            </div>
            <div className="settings-content">
              <div className="settings-content-header">
                <h3>{activeSettingsTab} Settings</h3>
                <button onClick={() => setIsSettingsOpen(false)}>
                  <X size={20} />
                </button>
              </div>
              <div className="settings-center">
                <div className="toggle-graphic">
                  <div className="toggle-track">
                    <div className="toggle-thumb"></div>
                  </div>
                </div>
                <p>it will be soon</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ===== SIDEBAR ===== */}
      <aside className="sidebar">
        <div className="logo">
          <Sparkles size={22} className="logo-icon" strokeWidth={2} />
          <span className="logo-text">ChatBox</span>
        </div>

        <button className="new-chat-btn" onClick={resetChat}>
          <Plus size={16} strokeWidth={2.5} />
          New Chat +
        </button>

        <div className="history-section">
          <span className="history-label">CHAT HISTORY</span>
          <div className="history-divider" />
          <div className="empty-state">
            <div className="empty-icon-wrapper">
              <MessageSquare size={22} strokeWidth={1.8} />
            </div>
            <p className="empty-text">No recent conversations.</p>
          </div>
        </div>

        <div className="user-footer">
          <div className="user-info">
            <div className="avatar">RD</div>
            <div className="user-details">
              <span className="user-name">name of user</span>
              <span className="user-role">Ryan Developer</span>
            </div>
          </div>
          <button
            className="gear-btn"
            aria-label="Settings"
            onClick={() => setIsSettingsOpen(true)}
          >
            <Settings size={18} strokeWidth={1.8} />
          </button>
        </div>
      </aside>

      {/* ===== MAIN CONTENT ===== */}
      <main className="main-content">
        <div className={`center-area ${isChatEmpty ? "empty" : "has-messages"}`}>
          {isChatEmpty && (
            <h1 className="main-title">
              What Can <span className="neo-highlight">Chatty</span> Help You With Today?
            </h1>
          )}

          <div className="message-list">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`message ${msg.role === "user" ? "user" : "assistant"}`}
              >
                <div className="bubble">
                  {msg.file && (
                    <div className="file-attachment">
                      {msg.file.dataURL && msg.file.type.startsWith("image/") ? (
                        <img src={msg.file.dataURL} alt="Uploaded" className="file-preview-img" />
                      ) : (
                        <div className="file-icon">
                          <File size={20} />
                          <span>{msg.file.name}</span>
                        </div>
                      )}
                      <button
                        className="remove-file-btn"
                        onClick={() => deleteMessage(msg.id)}
                        aria-label="Remove file"
                      >
                        <X size={14} />
                      </button>
                    </div>
                  )}
                  {msg.text && <span>{msg.text}</span>}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <div className={`input-wrapper ${isChatEmpty ? "empty-state" : ""}`}>
            <div className="input-container">
              <div className="input-row">
                <input
                  type="text"
                  className="text-input"
                  placeholder="Ask anything you want..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                />
                <div className="input-actions">
                  <button
                    className={`icon-btn ${isListening ? "listening" : ""}`}
                    onClick={toggleListening}
                    aria-label="Voice input"
                  >
                    <Mic size={18} strokeWidth={1.8} />
                  </button>
                  <button
                    className="icon-btn"
                    onClick={() => setIsUploadPanelOpen(true)}
                    aria-label="Attach file"
                  >
                    <Paperclip size={18} strokeWidth={1.8} />
                  </button>
                  <button className="send-btn" onClick={handleSend}>
                    <ArrowUp size={18} strokeWidth={2.5} />
                  </button>
                </div>
              </div>
            </div>

            {isChatEmpty && (
              <div className="actions-row">
                <button
                  className="action-btn"
                  onClick={() => handlePillClick("Create an image of a futuristic city")}
                >
                  <Image size={16} strokeWidth={1.8} />
                  Create Image
                </button>
                <button
                  className="action-btn"
                  onClick={() => handlePillClick("Summarize this text for me: ")}
                >
                  <FileText size={16} strokeWidth={1.8} />
                  Summarize Text
                </button>
                <button
                  className="action-btn"
                  onClick={() => handlePillClick("Surprise me with a fun fact about space")}
                >
                  <Wand2 size={16} strokeWidth={1.8} />
                  Surprise Me
                </button>
                <button
                  className="action-btn"
                  onClick={() => handlePillClick("Make a plan for my upcoming project")}
                >
                  <Lightbulb size={16} strokeWidth={1.8} />
                  Make a plan
                </button>
                <button className="action-btn more-btn">More</button>
              </div>
            )}
          </div>

          <div className="main-footer">
            <span>Chatty can make mistakes. Check important info.</span>
          </div>
        </div>
      </main>

      {/* ===== UPLOAD SLIDE PANEL ===== */}
      {isUploadPanelOpen && (
        <>
          <div
            className="upload-overlay"
            onClick={() => setIsUploadPanelOpen(false)}
          />
          <div className="upload-panel">
            <div className="upload-header">
              <h4>Upload & Generate</h4>
              <button onClick={() => setIsUploadPanelOpen(false)}>
                <X size={18} />
              </button>
            </div>
            <div className="upload-body">
              <div className="upload-section">
                <label>Upload File</label>
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileChange}
                />
              </div>

              {uploadedFile && (
                <div className="file-preview">
                  {filePreview ? (
                    <img src={filePreview} alt="Preview" className="preview-image" />
                  ) : (
                    <div className="file-icon-wrapper">
                      <File size={32} />
                      <span>{uploadedFile.name}</span>
                    </div>
                  )}
                  <button onClick={clearFile} className="remove-file">✕</button>
                </div>
              )}

              <div className="gen-section">
                <button className="gen-btn" onClick={() => handleGenClick("Audio")}>
                  <AudioWaveform size={16} />
                  Gen Audio
                </button>
                <button className="gen-btn" onClick={() => handleGenClick("Image")}>
                  <Image size={16} />
                  Gen Image
                </button>
                <button className="gen-btn" onClick={() => handleGenClick("Code")}>
                  <Code size={16} />
                  Gen Code
                </button>
                <button className="gen-btn" onClick={() => handleGenClick("Video")}>
                  <Video size={16} />
                  Gen Video
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}