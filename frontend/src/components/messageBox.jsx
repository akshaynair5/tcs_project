import React, { useState, useEffect, useRef } from 'react';
import userImage from "../assets/user.png";
import assistantImage from "../assets/bot.png";
import ReactMarkdown from 'react-markdown';

const MessageBox = ({ content, role }) => {
  const isUser = role === "user";
  const isAssistant = role === "assistant" || role === "ai_assistant" || role === "system";

  const profileImage = isUser ? userImage : assistantImage;

  const isToggleContent = isAssistant && typeof content === "object" && content.response_short && content.response_detailed;

  const [showDetailed, setShowDetailed] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const utteranceRef = useRef(null);

  const messageText = isToggleContent
    ? (showDetailed ? content.response_detailed : content.response_short)
    : content;

  const handleReadAloud = () => {
    if ('speechSynthesis' in window) {
      // Stop if already speaking
      if (window.speechSynthesis.speaking || isSpeaking) {
        window.speechSynthesis.cancel();
        setIsSpeaking(false);
        return;
      }

      const utterance = new SpeechSynthesisUtterance(messageText);
      utterance.lang = 'en-US';
      utterance.rate = 1;
      utterance.pitch = 1;

      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);

      utteranceRef.current = utterance;
      setIsSpeaking(true);
      window.speechSynthesis.speak(utterance);
    } else {
      alert("Speech synthesis is not supported in this browser.");
    }
  };

  useEffect(() => {
    return () => {
      // Cleanup when component unmounts
      window.speechSynthesis.cancel();
    };
  }, []);

  return (
    <div className={`flex text-left gap-3 w-[75vw] ${isUser ? "flex-row-reverse items-end" : "items-start"} animate-fade-in`}>
      <img
        src={profileImage}
        alt="profile"
        className="w-8 h-8 rounded-full border-2 border-gray-400"
      />
      <div className="flex flex-col gap-1">
        <div
          className={`p-3 max-w-xs md:max-w-md rounded-xl shadow-sm text-left ${
            isUser ? "bg-blue-500 text-white" : "bg-gray-200 text-black"
          }`}
        >
          <ReactMarkdown>{messageText}</ReactMarkdown>
        </div>
        
        {/* Button Container */}
        {isAssistant && (
          <div className="flex gap-3 ml-2">
            {isToggleContent && (
              <button
                onClick={() => setShowDetailed(!showDetailed)}
                className="text-xs text-blue-500 hover:underline"
              >
                {showDetailed ? "Show Less" : "Show More"}
              </button>
            )}
            <button
              onClick={handleReadAloud}
              className="text-xs text-green-600 hover:underline"
            >
              {isSpeaking ? "Stop Reading" : "Read Aloud"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default MessageBox;
