import { Copy, Trash2, ExternalLink } from 'lucide-react';

import toast from 'react-hot-toast';

interface URLItem {
    id: string;
    short_code: string;
    long_url: string;
    click_count: number;
    created_at: string;
}

interface URLListProps {
    urls: URLItem[];
    onDelete: (shortCode: string) => void;
}

export function URLList({ urls, onDelete }: URLListProps) {
    const copyToClipboard = (shortCode: string) => {
        const url = `${window.location.protocol}//${window.location.host}/${shortCode}`;
        navigator.clipboard.writeText(url);
        toast.success('Copied to clipboard!');
    };

    if (urls.length === 0) {
        return (
            <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-200">
                <p className="text-gray-500">No URLs yet. Create one above!</p>
            </div>
        );
    }

    return (
        <div className="bg-white shadow-sm rounded-lg border border-gray-200 overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                    <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Short Link</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Original URL</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Clicks</th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                    </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                    {urls.map((url) => (
                        <tr key={url.id} className="hover:bg-gray-50 transition-colors">
                            <td className="px-6 py-4 whitespace-nowrap">
                                <div className="flex items-center text-primary-600 font-medium">
                                    <span className="mr-2">/{url.short_code}</span>
                                    <button onClick={() => copyToClipboard(url.short_code)} className="text-gray-400 hover:text-primary-600 transition-colors">
                                        <Copy size={16} />
                                    </button>
                                </div>
                            </td>
                            <td className="px-6 py-4">
                                <div className="flex items-center max-w-xs">
                                    <span className="truncate text-gray-500 text-sm block">{url.long_url}</span>
                                    <a href={url.long_url} target="_blank" rel="noopener noreferrer" className="ml-2 text-gray-400 hover:text-gray-600">
                                        <ExternalLink size={14} />
                                    </a>
                                </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                    {url.click_count}
                                </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                <button
                                    onClick={() => onDelete(url.short_code)}
                                    className="text-red-400 hover:text-red-600 transition-colors p-2 rounded-full hover:bg-red-50"
                                >
                                    <Trash2 size={18} />
                                </button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}