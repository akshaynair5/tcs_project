import { useContext, useState } from "react";
import { AuthContext } from "../contextProvider";
import axios from "axios";
import { motion, AnimatePresence } from "framer-motion";

const ChatSidebar = () => {
    const { currentUserData, currentChat, setCurrentChat, currentUser } = useContext(AuthContext);
    const [newChatTitle, setNewChatTitle] = useState("");

    const createChat = async () => {
        if (!newChatTitle.trim()) return;

        try {
            const response = await axios.post("http://127.0.0.1:5000/api/chat", {
                user_id: currentUser.user_id,
                title: newChatTitle,
            });

            if (response.status === 201) {
                setCurrentChat({
                    _id: response.data.chat_id,
                    title: newChatTitle,
                    lastMessage: "",
                    lastMessageTime: "Just now",
                });

                setNewChatTitle("");
            }
        } catch (error) {
            console.error("Failed to create chat", error);
        }
    };

    return (
        <aside className="w-[20vw] h-screen bg-[#1a1a1e] text-white p-4 overflow-y-auto z-10 flex flex-col border-r border-[#2a2a2e] shadow-lg">
            <h2 className="text-2xl font-bold mb-6 text-[#cbd5e1] tracking-wide">Chats</h2>

            {/* New Chat Input */}
            <div className="mb-6 flex rounded-lg overflow-hidden border border-[#333] shadow-sm">
                <input
                    type="text"
                    placeholder="Start a new chat..."
                    value={newChatTitle}
                    onChange={(e) => setNewChatTitle(e.target.value)}
                    className="flex-grow p-2 bg-[#26262b] text-white placeholder-gray-400 focus:outline-none"
                />
                <button
                    onClick={createChat}
                    className="bg-[#3b82f6] px-4 text-white font-bold hover:bg-[#2563eb] transition"
                >
                    +
                </button>
            </div>

            {/* Chat List */}
            <ul className="flex-grow overflow-auto space-y-2">
                {currentUserData?.chats?.length > 0 ? (
                    <AnimatePresence>
                        {currentUserData.chats.map((chat) => (
                            <motion.li
                                key={chat._id}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -10 }}
                                transition={{ duration: 0.2 }}
                                className={`p-4 rounded-xl cursor-pointer transition-all duration-200 
                                    ${currentChat?._id === chat._id
                                        ? "bg-[#2563eb] text-white"
                                        : "bg-[#2a2a2e] hover:bg-[#313136] text-gray-200"}`}
                                onClick={() => setCurrentChat(chat)}
                            >
                                <div className="flex justify-between items-center mb-1">
                                    <span className="font-semibold truncate">{chat.title}</span>
                                    <span className="text-xs text-gray-400 whitespace-nowrap">
                                        {chat.lastMessageTime
                                            ? new Date(chat.lastMessageTime).toLocaleString("en-US", {
                                                  weekday: "short",
                                                  hour: "2-digit",
                                                  minute: "2-digit",
                                              })
                                            : "No messages"}
                                    </span>
                                </div>
                                <p className="text-sm text-gray-400 truncate">
                                    {chat.lastMessage?.response_with_context
                                        ? chat.lastMessage.response_with_context
                                        : chat.lastMessage || "Start chatting..."}
                                </p>
                            </motion.li>
                        ))}
                    </AnimatePresence>
                ) : (
                    <p className="text-gray-500 text-sm text-center mt-10">No chats available</p>
                )}
            </ul>
        </aside>
    );
};

export default ChatSidebar;
