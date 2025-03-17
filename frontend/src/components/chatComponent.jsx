import { useState } from "react";
import MessageBox from "./messageBox";
import { Send } from "lucide-react";
import ChatInput from "./chatBar";

const ChatComponent = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false); 

  const handleSend = async () => {
    if (!input.trim()) return;

    const newMessage = { text: input, sender: "user" };
    setMessages((prevMessages) => [...prevMessages, newMessage]);
    
    setLoading(true);

    try {
      const response = await fetch("http://127.0.0.1:5000/api/chat/ask", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question: input }),
      });

      const data = await response.json();

      if (response.ok) {
        const assistantMessage = { text: data.answer, sender: "assistant" };
        setMessages((prevMessages) => [...prevMessages, assistantMessage]);
      } else {
        const errorMessage = {
          text: data.error || "Something went wrong",
          sender: "assistant",
        };
        setMessages((prevMessages) => [...prevMessages, errorMessage]);
      }
    } catch (error) {
      console.error("Error:", error);
      const errorMessage = { text: "Server is not responding", sender: "assistant" };
      setMessages((prevMessages) => [...prevMessages, errorMessage]);
    }
    setInput("");
    setLoading(false);
  };

  return (
    <div className="flex flex-col h-screen bg-transparent p-4">
      {/* Chat Messages */}
      <div className="flex flex-col overflow-y-auto mb-4 space-y-4 h-screen w-screen">
        {messages.map((msg, index) => (
          <MessageBox key={index} text={msg.text} sender={msg.sender} />
        ))}

        {loading && (
          <div className="text-center text-gray-500 text-sm animate-pulse">
            Typing...
          </div>
        )}
      </div>

      <div className="flex items-center gap-2 p-3 bg-white border-t border-gray-300">
        <input
          type="text"
          className="flex-1 p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Type your message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
        />
        <button
          className="p-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition"
          onClick={handleSend}
          disabled={loading}
        >
          <Send size={20} />
        </button>
      </div>
      {/* <ChatInput onSend={handleSend} /> */}
    </div>
  );
};

export default ChatComponent;
