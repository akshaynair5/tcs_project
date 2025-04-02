import { useContext, useState} from 'react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Home from './pages/home'
import './App.css'
import Login from './pages/login'
import Register from './pages/register'
import { AuthContext} from './contextProvider'
import { Navigate } from "react-router-dom";
import AdminPanel from './pages/adminPanel'


function App() {

  const ProtectedRoute = ({ children }) => {
    const { currentUser } = useContext(AuthContext);
    // if (!currentUser) {
    //   return <Navigate to="/login" />;
    // }

    return children;
  };

  return (
    <>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<ProtectedRoute><Home/></ProtectedRoute>} />
          <Route path="/register" element={<Register />} />
          <Route path="/login" element={<Login />} />
          <Route path="/admin" element={<AdminPanel></AdminPanel>} />
        </Routes>
      </BrowserRouter>
    </>
  )
}

export default App
