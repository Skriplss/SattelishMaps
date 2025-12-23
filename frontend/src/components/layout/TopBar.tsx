import { Calendar, Search, Bell, User } from 'lucide-react';
import { type ChangeEvent } from 'react';

interface TopBarProps {
    selectedDate: string;
    onDateChange: (date: string) => void;
}

export function TopBar({ selectedDate, onDateChange }: TopBarProps) {

    const handleDateChange = (e: ChangeEvent<HTMLInputElement>) => {
        onDateChange(e.target.value);
    };

    return (
        <div className="h-16 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between px-6 z-10 shadow-sm">

            {/* Left: Global Search (Placeholder) */}
            <div className="flex items-center gap-4 flex-1">
                <div className="relative w-64 hidden md:block">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <input
                        type="text"
                        placeholder="Search location..."
                        className="w-full pl-10 pr-4 py-2 bg-slate-100 dark:bg-slate-800 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all dark:text-slate-200"
                    />
                </div>
            </div>

            {/* Middle: Date Picker */}
            <div className="flex items-center gap-3">
                <div className="flex items-center bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg px-3 py-1.5 focus-within:ring-2 focus-within:ring-blue-500 transition-all">
                    <Calendar className="w-4 h-4 text-blue-600 dark:text-blue-400 mr-2" />
                    <input
                        type="date"
                        value={selectedDate}
                        onChange={handleDateChange}
                        className="bg-transparent border-none text-sm font-medium text-blue-700 dark:text-blue-300 focus:outline-none"
                    />
                </div>
            </div>

            {/* Right: User Actions */}
            <div className="flex items-center gap-4 flex-1 justify-end">
                <button className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full transition-colors relative">
                    <Bell className="w-5 h-5 text-slate-600 dark:text-slate-300" />
                    <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full border-2 border-white dark:border-slate-900"></span>
                </button>

                <div className="w-8 h-8 bg-gradient-to-tr from-purple-500 to-blue-500 rounded-full flex items-center justify-center text-white font-bold text-xs shadow-md cursor-pointer hover:shadow-lg transition-all">
                    <User className="w-4 h-4" />
                </div>
            </div>

        </div>
    );
}
