import { createContext, use, useEffect, useState } from "react";
import axios from "axios";
import logout from "./components/logout";
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
            console.log("Token found:", token);
            axios.post(
                "http://127.0.0.1:5000/api/verify-login",
                {}, 
                {
                    headers: {
                        Authorization: `Bearer ${token}`, 
                        "Content-Type": "application/json",
                    }
                }
            )
            .then((res) => {
                console.log("API Response:", res.data);
                if (res.data && !res.data?.error) {
                    setCurrentUser(res.data);
                    // window.location.href = "/";
                } else {
                    console.warn("Invalid token or user data:", res.data);
                    logout();
                }
            })
            .catch((error) => {
                console.error("Login verification failed:", error);
            });
        }
        else{
            console.log("No token found");
            if(window.location.pathname !== "/login" && window.location.pathname !== "/register"){
                window.location.href = "/login";
            }
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


    return (
        <AuthContext.Provider value={{ currentUser, login, currentUserData, setCurrentUserData, currentChat, setCurrentChat }}>
            {children}
        </AuthContext.Provider>
    );
};
