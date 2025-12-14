import { useState } from 'react';
import client from '../api/client';
import { Button } from './ui/Button';
import { Input } from './ui/Input';
import toast from 'react-hot-toast';

interface CreateURLFormProps {
    onSuccess: () => void;
}

export function CreateURLForm({ onSuccess }: CreateURLFormProps) {
    const [longUrl, setLongUrl] = useState('');
    const [alias, setAlias] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        try {
            await client.post('/urls/', {
                long_url: longUrl,
                custom_alias: alias || undefined
            });
            toast.success('URL Shortened!');
            setLongUrl('');
            setAlias('');
            onSuccess();
        } catch (error) {
            toast.error('Failed to shorten URL. Alias might be taken.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 mb-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Shorten a new URL</h3>
            <div className="flex flex-col md:flex-row gap-4">
                <div className="flex-grow">
                    <Input
                        placeholder="https://example.com/very-long-url..."
                        value={longUrl}
                        onChange={(e) => setLongUrl(e.target.value)}
                        required
                    />
                </div>
                <div className="md:w-48">
                    <Input
                        placeholder="Alias (optional)"
                        value={alias}
                        onChange={(e) => setAlias(e.target.value)}
                    />
                </div>
                <Button type="submit" disabled={isLoading}>
                    {isLoading ? 'Shortening...' : 'Shorten'}
                </Button>
            </div>
        </form>
    );
}