import { createContext, use, useEffect, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

// Create Context
export const AuthContext = createContext();

// Provider Component
export const AuthContextProvider = ({ children }) => {
    const [currentUser, setCurrentUser] = useState(null);
    const [currentUserData, setCurrentUserData] = useState(null);
    const [currentChat, setCurrentChat] = useState(null);
    // Load user from localStorage on mount
    useEffect(() => {
        const token = localStorage.getItem("token");
        if (token) {
            axios.post(
                "http://127.0.0.1:5000/api/verify-login",
                {}, // Empty body (POST still works)
                {
                    headers: {
                        Authorization: `Bearer ${token}`, 
                        "Content-Type": "application/json",
                    },
                    withCredentials: true, // Important for sending cookies if needed
                }
            )
            .then((res) => {
                if (res.data.error) {
                    console.log(res);
                    logout();
                } else {
                    setCurrentUser(res.data);
                }
            })
            .catch(() => {
                logout();
            });
        }
    }, []);

    useEffect(() => {
        if (currentUser) {
            axios
                .get(`http://127.0.0.1:5000/api/user/${currentUser.user_id}/chats`)
                .then((res) => setCurrentUserData(res.data))  // Store chats in state
                .catch((err) => console.error("Error fetching chats:", err));
        }
    }, [currentUser]);

    useEffect(()=>{
        console.log(currentUserData)
    },[currentUserData])

    useEffect(() => {
        if (currentUserData) {
            setCurrentChat(currentUserData.chats[0]);
        }
    }, [currentUserData]);

    // Login function
    const login = async (email, password) => {
        try {
            const response = await axios.post("http://127.0.0.1:5000/api/login", {
                email,
                password,
            });
            localStorage.setItem("token", response.data.token);
            console.log(response.data);
            setCurrentUser(response.data.user);
            alert("Login successful!");
            return response;
        } catch (err) {
            console.log(err)
            throw new Error(err.response?.data?.error || "Invalid credentials.");
        }
    };

    // Logout function
    const logout = () => {
        const navigate = useNavigate();
        localStorage.removeItem("token");
        setCurrentUser(null);
        navigate("/login");
    };

    return (
        <AuthContext.Provider value={{ currentUser, login, logout, currentUserData, setCurrentUserData, currentChat, setCurrentChat }}>
            {children}
        </AuthContext.Provider>
    );
};
