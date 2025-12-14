import { useEffect, useState } from 'react';
import client from '../api/client';
import { Navbar } from '../components/Navbar';
import { CreateURLForm } from '../components/CreateURLForm';
import { URLList } from '../components/URLList';

export default function Dashboard() {
    const [urls, setUrls] = useState([]);

    const fetchUrls = async () => {
        try {
            const response = await client.get('/urls/');
            setUrls(response.data.urls);
        } catch (error) {
            console.error('Failed to fetch URLs');
        }
    };

    useEffect(() => {
        fetchUrls();
    }, []);

    const handleDelete = async (shortCode: string) => {
        if (confirm('Are you sure you want to delete this URL?')) {
            try {
                await client.delete(`/urls/${shortCode}`);
                fetchUrls(); // Refresh list
            } catch (error) {
                console.error('Failed to delete');
            }
        }
    };

    return (
        <div className="min-h-screen bg-gray-50">
            <Navbar />

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <CreateURLForm onSuccess={fetchUrls} />
                <URLList urls={urls} onDelete={handleDelete} />
            </main>
        </div>
    );
}