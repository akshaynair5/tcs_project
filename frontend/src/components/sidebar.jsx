import { useContext, useState, useEffect } from "react";
import { AuthContext } from "../contextProvider";
import axios from "axios";
import { motion, AnimatePresence } from "framer-motion";
import { Trash2 } from "lucide-react";
import { Plus } from "lucide-react";

const ChatSidebar = () => {
    const { currentUserData, currentChat, setCurrentChat, currentUser } = useContext(AuthContext);
    const [newChatTitle, setNewChatTitle] = useState("");
    const [chats, setChats] = useState([]);

    useEffect(() => {
        if (currentUserData?.chats) {
            setChats(currentUserData.chats);
        }
    }, [currentUserData]);

    const createChat = async () => {
        if (!newChatTitle.trim()) return;

        try {
            const response = await axios.post("http://127.0.0.1:5000/api/chat", {
                user_id: currentUser.user_id,
                title: newChatTitle,
            });

            if (response.status === 201) {
                const newChat = {
                    _id: response.data.chat_id,
                    title: newChatTitle,
                    lastMessage: "",
                    lastMessageTime: "Just now",
                };

                setChats([newChat, ...chats]); // Add new chat to top
                setCurrentChat(newChat);
                setNewChatTitle("");
            }
        } catch (error) {
            console.error("Failed to create chat", error);
        }
    };

    const deleteChat = async (chatId) => {
        try {
            await axios.delete(`http://127.0.0.1:5000/api/chat/${chatId}`);
            const updatedChats = chats.filter((chat) => chat._id !== chatId);
            setChats(updatedChats);

            if (currentChat?._id === chatId) {
                setCurrentChat(null); // clear selection if deleted
            }
        } catch (error) {
            console.error("Failed to delete chat", error);
        }
    };

    return (
        <aside className="w-[20vw] h-screen bg-[#1a1a1e] text-white p-4 overflow-y-auto z-10 flex flex-col border-r border-[#2a2a2e] shadow-lg">
            <h2 className="text-2xl font-bold mb-6 text-[#cbd5e1] tracking-wide">Chats</h2>

            {/* New Chat Input */}
            <motion.div
                className="mb-6 flex rounded-lg overflow-hidden border border-[#333] shadow-md backdrop-blur-sm"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4 }}
                >
                <motion.input
                    type="text"
                    placeholder="Start a new chat..."
                    value={newChatTitle}
                    onChange={(e) => setNewChatTitle(e.target.value)}
                    whileFocus={{ scale: 1.02 }}
                    className="flex-grow p-2 bg-[#1f1f24] text-white placeholder-gray-500 focus:outline-none transition-all duration-200"
                />
                <motion.button
                    onClick={createChat}
                    whileTap={{ scale: 0.9 }}
                    whileHover={{ backgroundColor: "#1d4ed8", rotate: 0.5 }}
                    className="bg-[#3b82f6] px-4 flex items-center justify-center text-white font-bold hover:bg-[#2563eb] transition-all duration-200"
                >
                    <Plus className="w-5 h-5" />
                </motion.button>
            </motion.div>

            {/* Chat List */}
            <ul className="flex-grow overflow-auto space-y-2">
                {chats.length > 0 ? (
                    <AnimatePresence>
                    {chats.map((chat) => (
                        <motion.li
                        key={chat._id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        transition={{ duration: 0.2 }}
                        className={`p-4 rounded-xl transition-all duration-200 relative group flex flex-col justify-between
                            ${currentChat?._id === chat._id
                            ? "bg-[#2563eb] text-white"
                            : "bg-[#2a2a2e] hover:bg-[#313136] text-gray-200"}`}
                        >
                        {/* Chat Content */}
                        <div
                            className="flex-1 cursor-pointer"
                            onClick={() => setCurrentChat(chat)}
                        >
                            <span className="font-semibold truncate block">{chat.title}</span>
                            <span className="text-xs text-gray-400 whitespace-nowrap">
                            {chat.lastMessageTime
                                ? new Date(chat.lastMessageTime).toLocaleString("en-US", {
                                    weekday: "short",
                                    hour: "2-digit",
                                    minute: "2-digit",
                                })
                                : "No messages"}
                            </span>
                            <p className="text-sm text-gray-400 truncate mt-1">
                            {chat.lastMessage?.response_with_context
                                ? chat.lastMessage.response_with_context
                                : chat.lastMessage || "Start chatting..."}
                            </p>
                        </div>

                        {/* Delete Button at Bottom Right */}
                        <div className="flex justify-end mt-3">
                            <button
                            onClick={() => deleteChat(chat._id)}
                            className="text-gray-400 hover:text-red-500"
                            title="Delete chat"
                            >
                            <Trash2 size={16} />
                            </button>
                        </div>
                        </motion.li>
                    ))}
                    </AnimatePresence>
                ) : (
                    <p className="text-gray-500 text-sm mt-4 text-center">No chats yet.</p>
                )}
            </ul>

        </aside>
    );
};

export default ChatSidebar;
