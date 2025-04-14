import { useState, useEffect, useRef } from "react";
import { Send, Mic, MicOff } from "lucide-react";
import { motion } from "framer-motion";

const ChatInput = ({ onSend }) => {
  const [message, setMessage] = useState("");
  const [listening, setListening] = useState(false);
  const recognitionRef = useRef(null);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert("Speech Recognition is not supported in this browser.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";

    recognition.onresult = (event) => {
      let interimTranscript = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          setMessage((prev) => prev + transcript);
        } else {
          interimTranscript += transcript;
        }
      }
    };

    recognition.onend = () => {
      setListening(false);
    };

    recognitionRef.current = recognition;
  }, []);

  const toggleListening = () => {
    if (listening) {
      recognitionRef.current?.stop();
      setListening(false);
    } else {
      recognitionRef.current?.start();
      setListening(true);
    }
  };

  const handleSend = async () => {
    if (message.trim()) {
      await onSend(message);
      setMessage("");
    }
  };

  return (
    <div className="fixed bottom-4 w-[70vw] left-[60vw] -translate-x-1/2 z-20">
      <div className="flex items-center gap-2 bg-[#2a2a2e] border border-[#333] shadow-md px-4 py-2 rounded-2xl backdrop-blur-md">
        <input
          type="text"
          className="flex-1 bg-transparent text-white placeholder-gray-400 outline-none px-2 py-2 rounded-md"
          placeholder="Type your message..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
        />

        {/* Mic Button */}
        <motion.button
          whileTap={{ scale: 0.9 }}
          whileHover={{ scale: 1.05 }}
          className={`p-2 rounded-lg transition duration-150 ${
            listening ? "bg-red-500 hover:bg-red-600" : "bg-green-600 hover:bg-green-700"
          }`}
          onClick={toggleListening}
        >
          {listening ? <MicOff size={20} color="white" /> : <Mic size={20} color="white" />}
        </motion.button>

        {/* Send Button */}
        <motion.button
          whileTap={{ scale: 0.9 }}
          whileHover={{ scale: 1.05 }}
          className="bg-[#2563eb] p-2 rounded-lg text-white hover:bg-[#1d4ed8] transition duration-150"
          onClick={handleSend}
        >
          <Send size={20} />
        </motion.button>
      </div>
    </div>
  );
};

export default ChatInput;
