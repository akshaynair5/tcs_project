import { useContext, useEffect, useState } from "react";
import MessageBox from "./messageBox";
import { Send } from "lucide-react";
import ChatInput from "./chatBar";
import FileUpload from "./fileUpload";
import { AuthContext } from "../contextProvider";
import axios from "axios";

const ChatComponent = () => {
  const {currentUser, currentChat} = useContext(AuthContext);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false); 

  useEffect(()=>{
    if(currentChat && currentChat.messages){
      setMessages(currentChat.messages);
    }
  },[currentChat])

  const handleSend = async () => {
    if (!input.trim()) return;
  
    // Fix: Use correct keys (`content` instead of `text`, `role` instead of `sender`)
    const newMessage = { content: input, role: "user" };
    setMessages((prevMessages) => [...prevMessages, newMessage]);
  
    setLoading(true);
  
    try {
      const { data } = await axios.post("http://127.0.0.1:5000/api/ask", {
        chat_id: currentChat._id,
        user_id: currentUser.user_id,
        question: input,
      });
  
      // Fix: Ensure assistant response structure matches what `MessageBox` expects
      console.log(data.answer)
      const assistantMessage = { content: data.answer, role: "ai_assistant" };
      setMessages((prevMessages) => [...prevMessages, assistantMessage]);
    } catch (error) {
      console.error("Error:", error);
  
      const errorMessage = {
        content: error.response?.data?.error || "Something went wrong",
        role: "ai_assistant",
      };
  
      setMessages((prevMessages) => [...prevMessages, errorMessage]);
    }
  
    setInput("");
    setLoading(false);
  };

  return (
    <div className="flex flex-col h-[75vh] bg-transparent p-4 fixed w-[80vw] left-[20vw] top-[12vh] overflow-y-scroll overflow-x-hidden">
      {/* Chat Messages */}
      <div className="flex flex-col overflow-y-auto mb-4 space-y-4 h-screen w-screen">
        {messages.map((msg, index) => (
          <MessageBox key={index} content={msg.content} role={msg.role} />
        ))}

        {loading && (
          <div className="text-center text-gray-500 text-sm animate-pulse">
            Typing...
          </div>
        )}
      </div>

      <div className="fixed top-[87vh] w-[75vw] flex items-center gap-2 p-3 bg-transparent">
        <input
          type="text"
          className="flex-1 p-2 border rounded-lg focus:outline-none focus:ring-1 focus:ring-gray-500"
          placeholder="Type your query..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
        />
        <button
          className="p-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition"
          onClick={handleSend}
          disabled={loading}
        >
          <Send size={20} />
        </button>
        <FileUpload />
      </div>
      {/* <ChatInput onSend={handleSend} /> */}
    </div>
  );
};

export default ChatComponent;
