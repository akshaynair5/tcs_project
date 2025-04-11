import { Link } from "react-router-dom";
import { useContext } from "react";
import { AuthContext } from "../contextProvider";
import logout from "./logout";

const Navbar = () => {
  const { currentUser } = useContext(AuthContext);

  return (
    <nav className="fixed top-0 left-0 w-full h-[10vh] bg-[#1a1a1e] text-white flex items-center px-6 shadow-md z-20">
      <div className="container mx-auto flex justify-between items-center">
        <Link className="text-2xl font-semibold tracking-wide hover:text-gray-300 transition" to="/">
          Chat
        </Link>

        <div className="flex items-center gap-4">
          {currentUser?.email && (
            <span className="text-sm text-gray-400 hidden md:block">
              Signed in as <span className="text-white font-medium">{currentUser.email}</span>
            </span>
          )}
          <button
            className="px-4 py-1.5 text-sm rounded-md bg-red-600 hover:bg-red-700 transition"
            onClick={logout}
          >
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
