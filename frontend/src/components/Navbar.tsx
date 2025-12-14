import { Link } from 'react-router-dom';
import { LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { Button } from './ui/Button';

export function Navbar() {
    const { user, logout } = useAuth();

    return (
        <header className="bg-white shadow-sm">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
                <Link to="/" className="text-2xl font-bold text-primary-600">Shorty</Link>
                <div className="flex items-center gap-4">
                    <span className="text-gray-600 text-sm hidden sm:inline">Hello, {user?.email}</span>
                    <Button variant="ghost" onClick={logout} className="flex items-center gap-2">
                        <LogOut size={16} />
                        Logout
                    </Button>
                </div>
            </div>
        </header>
    );
}