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
  Sun,
  Moon,
  Monitor,
  Globe,
  Type,
  ToggleLeft,
  ToggleRight,
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

  // Backend state
  const [backendStatus, setBackendStatus] = useState({
    online: false,
    message: "Connecting…",
    device: "",
  });
  const [isGenerating, setIsGenerating] = useState(false);

  // Settings state (persisted in localStorage)
  const [settings, setSettings] = useState(() => {
    const saved = localStorage.getItem("chat_settings");
    return saved
      ? JSON.parse(saved)
      : {
          theme: "dark",
          language: "en",
          fontSize: 14,
          animations: true,
          notifications: true,
        };
  });

  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);
  const fileInputRef = useRef(null);

  // ===== EFFECTS =====
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Save settings to localStorage
  useEffect(() => {
    localStorage.setItem("chat_settings", JSON.stringify(settings));
    // Apply theme to body
    document.body.style.backgroundColor = settings.theme === "dark" ? "#0b0e14" : "#f0f2f5";
    document.body.style.color = settings.theme === "dark" ? "#e5e9f0" : "#1a1f2a";
  }, [settings]);

  // Ping backend health on mount
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch("http://localhost:5000/api/health");
        const data = await res.json();
        setBackendStatus({
          online: true,
          message: data.message || "Connected successfully!",
          device: data.device || "unknown",
        });
      } catch {
        setBackendStatus({
          online: false,
          message: "Could not connect to backend",
          device: "",
        });
      }
    };
    checkHealth();
  }, []);

  // ===== SPEECH RECOGNITION (auto‑detect) =====
  const startListening = () => {
    if (!("webkitSpeechRecognition" in window) && !("SpeechRecognition" in window)) {
      alert("Speech recognition is not supported in your browser.");
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = "";
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

  // ===== BACKEND GENERATION =====
  const generateFromBackend = async (prompt) => {
    setIsGenerating(true);
    try {
      const response = await fetch("http://localhost:5000/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt: prompt,
          ratio: "1:1",
          steps: 50,
        }),
      });
      if (!response.ok) throw new Error("Generation failed");
      const data = await response.json();
      // Expecting { image: "base64_string" }
      if (data.image) {
        return `data:image/png;base64,${data.image}`;
      } else {
        throw new Error("No image in response");
      }
    } catch (error) {
      console.error("Generation error:", error);
      return null;
    } finally {
      setIsGenerating(false);
    }
  };

  // ===== HANDLERS =====
  const handleSend = async () => {
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

    // Send to backend if we have a prompt
    let assistantText = "";
    let assistantImage = null;

    if (text) {
      const imageDataUrl = await generateFromBackend(text);
      if (imageDataUrl) {
        assistantImage = imageDataUrl;
        assistantText = "Here's your generated image:";
      } else {
        assistantText = "Sorry, I couldn't generate an image. Please try again.";
      }
    } else {
      assistantText = "Please give me a moment.";
    }

    // Add assistant message with typing effect (if no image) or direct
    const assistantId = Date.now() + 1;
    setMessages((prev) => [
      ...prev,
      {
        id: assistantId,
        role: "assistant",
        text: assistantText,
        image: assistantImage,
      },
    ]);

    // If text is plain (no image), apply typing effect
    if (!assistantImage && assistantText) {
      let index = 0;
      const fullResponse = assistantText;
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantId ? { ...msg, text: "" } : msg
        )
      );
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
    }
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

  const genTypes = [
    { id: "Audio", icon: AudioWaveform, label: "Gen Audio" },
    { id: "Image", icon: Image, label: "Gen Image" },
    { id: "Code", icon: Code, label: "Gen Code" },
    { id: "Video", icon: Video, label: "Gen Video" },
    { id: "Music", icon: AudioWaveform, label: "Gen Music" },
    { id: "Art", icon: Image, label: "Gen Art" },
    { id: "3D Model", icon: Image, label: "Gen 3D" },
    { id: "Presentation", icon: FileText, label: "Gen Slides" },
    { id: "Report", icon: FileText, label: "Gen Report" },
    { id: "Story", icon: FileText, label: "Gen Story" },
    { id: "Poem", icon: FileText, label: "Gen Poem" },
    { id: "Translation", icon: FileText, label: "Gen Translate" },
    { id: "Summary", icon: FileText, label: "Gen Summary" },
    { id: "Research", icon: FileText, label: "Gen Research" },
    { id: "Recipe", icon: FileText, label: "Gen Recipe" },
    { id: "Workout Plan", icon: FileText, label: "Gen Workout" },
    { id: "Travel Itinerary", icon: FileText, label: "Gen Itinerary" },
    { id: "Website", icon: Code, label: "Gen Website" },
    { id: "Mobile App", icon: Code, label: "Gen App" },
    { id: "Game", icon: Code, label: "Gen Game" },
  ];

  const handleGenClick = (type) => {
    // Map type to mock file data (same as before)
    const mockFileMap = {
      "Audio": { name: "generated_audio.mp3", type: "audio/mpeg" },
      "Image": { name: "generated_image.png", type: "image/png" },
      "Code": { name: "generated_code.py", type: "text/x-python" },
      "Video": { name: "generated_video.mp4", type: "video/mp4" },
      "Music": { name: "generated_music.mp3", type: "audio/mpeg" },
      "Art": { name: "generated_art.png", type: "image/png" },
      "3D Model": { name: "generated_3d.obj", type: "model/obj" },
      "Presentation": { name: "generated_slides.pptx", type: "application/vnd.openxmlformats-officedocument.presentationml.presentation" },
      "Report": { name: "generated_report.pdf", type: "application/pdf" },
      "Story": { name: "generated_story.txt", type: "text/plain" },
      "Poem": { name: "generated_poem.txt", type: "text/plain" },
      "Translation": { name: "generated_translation.txt", type: "text/plain" },
      "Summary": { name: "generated_summary.txt", type: "text/plain" },
      "Research": { name: "generated_research.pdf", type: "application/pdf" },
      "Recipe": { name: "generated_recipe.pdf", type: "application/pdf" },
      "Workout Plan": { name: "generated_workout.pdf", type: "application/pdf" },
      "Travel Itinerary": { name: "generated_itinerary.pdf", type: "application/pdf" },
      "Website": { name: "generated_website.zip", type: "application/zip" },
      "Mobile App": { name: "generated_app.zip", type: "application/zip" },
      "Game": { name: "generated_game.zip", type: "application/zip" },
    };

    const mock = mockFileMap[type];
    if (!mock) return;

    let dataURL = null;
    if (type === "Image" || type === "Art") {
      const canvas = document.createElement("canvas");
      canvas.width = 100;
      canvas.height = 100;
      const ctx = canvas.getContext("2d");
      const gradient = ctx.createLinearGradient(0, 0, 100, 100);
      gradient.addColorStop(0, "#ff6b6b");
      gradient.addColorStop(1, "#4ecdc4");
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, 100, 100);
      dataURL = canvas.toDataURL("image/png");
    }

    const mockFile = {
      name: mock.name,
      type: mock.type,
      dataURL: dataURL,
    };

    const userMsg = {
      id: Date.now(),
      role: "user",
      text: `Generate ${type}`,
      file: mockFile,
    };
    setMessages((prev) => [...prev, userMsg]);

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

  // ===== SETTINGS HANDLERS =====
  const updateSetting = (key, value) => {
    setSettings((prev) => ({ ...prev, [key]: value }));
  };

  const settingsTabs = [
    { id: "General", icon: Home },
    { id: "Account", icon: UserIcon },
    { id: "Appearance", icon: Palette },
    { id: "Notifications", icon: Bell },
  ];

  const isChatEmpty = messages.length === 0;

  // ===== RENDER =====
  return (
    <div className="app-container" style={{ backgroundColor: settings.theme === "dark" ? "#0b0e14" : "#f0f2f5" }}>
      {/* Settings Modal */}
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
              <div className="settings-body">
                {activeSettingsTab === "General" && (
                  <>
                    <div className="settings-item">
                      <label>Language</label>
                      <select
                        value={settings.language}
                        onChange={(e) => updateSetting("language", e.target.value)}
                      >
                        <option value="en">English</option>
                        <option value="es">Spanish</option>
                        <option value="fr">French</option>
                        <option value="hi">Hindi</option>
                        <option value="ml">Malayalam</option>
                      </select>
                    </div>
                    <div className="settings-item">
                      <label>Animations</label>
                      <button
                        className="toggle-btn"
                        onClick={() => updateSetting("animations", !settings.animations)}
                      >
                        {settings.animations ? <ToggleRight size={24} color="#3b7bff" /> : <ToggleLeft size={24} color="#6b7f94" />}
                      </button>
                    </div>
                  </>
                )}
                {activeSettingsTab === "Appearance" && (
                  <>
                    <div className="settings-item">
                      <label>Theme</label>
                      <select
                        value={settings.theme}
                        onChange={(e) => updateSetting("theme", e.target.value)}
                      >
                        <option value="dark">Dark</option>
                        <option value="light">Light</option>
                      </select>
                    </div>
                    <div className="settings-item">
                      <label>Font Size</label>
                      <input
                        type="range"
                        min="12"
                        max="20"
                        value={settings.fontSize}
                        onChange={(e) => updateSetting("fontSize", parseInt(e.target.value))}
                        style={{ width: "150px" }}
                      />
                      <span style={{ marginLeft: "8px" }}>{settings.fontSize}px</span>
                    </div>
                  </>
                )}
                {activeSettingsTab === "Notifications" && (
                  <div className="settings-item">
                    <label>Enable Notifications</label>
                    <button
                      className="toggle-btn"
                      onClick={() => updateSetting("notifications", !settings.notifications)}
                    >
                      {settings.notifications ? <ToggleRight size={24} color="#3b7bff" /> : <ToggleLeft size={24} color="#6b7f94" />}
                    </button>
                  </div>
                )}
                {activeSettingsTab === "Account" && (
                  <div className="settings-item">
                    <label>Profile</label>
                    <input type="text" placeholder="Username" defaultValue="RyanDeveloper" readOnly />
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Sidebar */}
      <aside className="sidebar" style={{ backgroundColor: settings.theme === "dark" ? "#11161e" : "#e8ecf2" }}>
        <div className="logo">
          <Sparkles size={22} className="logo-icon" strokeWidth={2} />
          <span className="logo-text" style={{ color: settings.theme === "dark" ? "#ffffff" : "#1a1f2a" }}>ChatBox</span>
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

      {/* Main Content */}
      <main className="main-content" style={{ backgroundColor: settings.theme === "dark" ? "#0b0e14" : "#f0f2f5" }}>
        {/* Backend Status Banner */}
        <div className={`status-banner ${backendStatus.online ? "online" : "offline"}`}>
          <span className="status-dot"></span>
          {backendStatus.online ? `✅ ${backendStatus.message}` : `❌ ${backendStatus.message}`}
          {backendStatus.device && ` (Device: ${backendStatus.device})`}
        </div>

        <div className={`center-area ${isChatEmpty ? "empty" : "has-messages"}`}>
          {isChatEmpty && (
            <h1 className="main-title">
              {settings.animations ? (
                "What Can Chatty Help You With Today?".split("").map((char, i) => (
                  <span
                    key={i}
                    className="wave-letter"
                    style={{
                      animationDelay: `${i * 0.05}s`,
                      display: "inline-block",
                    }}
                  >
                    {char === " " ? "\u00A0" : char}
                  </span>
                ))
              ) : (
                "What Can Chatty Help You With Today?"
              )}
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
                  {msg.image && (
                    <div className="generated-image-container">
                      <img src={msg.image} alt="Generated" className="generated-image" />
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
                  disabled={isGenerating}
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
                  <button className="send-btn" onClick={handleSend} disabled={isGenerating}>
                    {isGenerating ? "..." : <ArrowUp size={18} strokeWidth={2.5} />}
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

      {/* Upload Panel */}
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
                {genTypes.map(({ id, icon: Icon, label }) => (
                  <button
                    key={id}
                    className="gen-btn"
                    onClick={() => handleGenClick(id)}
                  >
                    <Icon size={16} />
                    {label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}