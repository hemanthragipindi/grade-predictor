import React, { useState, useEffect } from 'react';
import { useNavigate, Link, useLocation, useSearchParams } from 'react-router-dom';
import {
    ShoppingBag, Gavel, Clock, ChevronRight,
    TrendingUp, AlertCircle, CheckCircle2,
    Home, User, LogOut, Menu, X,
    Package, History, Search, Filter, Tag, MapPin,
    ShoppingCart, UserCheck, Heart, Calendar, Check, ShieldCheck, ShieldX, XCircle
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import marketService from '../services/market';
import buyerService from '../services/buyer';
import walletService from '../services/wallet';
import { useAuth } from '../context/AuthContext';
import SEO from '../components/common/SEO';
import NotificationBell from '../components/common/NotificationBell';
import NotificationsView from '../components/dashboard/NotificationsView';
import BuyerProfileForm from '../components/forms/BuyerProfileForm';

const getMediaUrl = (url) => {
    if (!url) return '';
    if (url.startsWith('http')) return url;
    const baseUrl = (import.meta.env.VITE_API_URL || 'http://localhost:9000/api/v1').replace('/api/v1', '');
    return `${baseUrl}${url}`;
};

// Live Countdown Timer Component
const CountdownTimer = ({ endTime }) => {
    const [timeLeft, setTimeLeft] = React.useState('');
    const [isExpired, setIsExpired] = React.useState(false);

    React.useEffect(() => {
        const update = () => {
            const now = new Date().getTime();
            const end = new Date(endTime).getTime();
            const diff = end - now;
            if (diff <= 0) {
                setTimeLeft('Ended');
                setIsExpired(true);
                return;
            }
            const days = Math.floor(diff / (1000 * 60 * 60 * 24));
            const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const mins = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
            const secs = Math.floor((diff % (1000 * 60)) / 1000);
            if (days > 0) setTimeLeft(`${days}d ${hours}h ${mins}m`);
            else if (hours > 0) setTimeLeft(`${hours}h ${mins}m ${secs}s`);
            else setTimeLeft(`${mins}m ${secs}s`);
        };
        update();
        const interval = setInterval(update, 1000);
        return () => clearInterval(interval);
    }, [endTime]);

    return (
        <span className={`flex items-center gap-1.5 ${isExpired ? 'text-red-500' : 'text-blue-500'}`}>
            <Clock size={14} className={isExpired ? 'text-red-400' : 'text-blue-400'} />
            {isExpired ? '⏰ Auction Ended' : `⏳ ${timeLeft}`}
        </span>
    );
};

const BuyerDashboard = () => {
    const navigate = useNavigate();
    const [searchParams, setSearchParams] = useSearchParams();
    const { accessToken, user, logout } = useAuth();
    const [bids, setBids] = useState([]);
    const [purchases, setPurchases] = useState([]);
    const [listings, setListings] = useState([]);
    const [wishlist, setWishlist] = useState([]);
    const [loading, setLoading] = useState(true);

    // Read from URL or default
    const activeTab = searchParams.get('tab') || 'dashboard';

    const setActiveTab = (tab) => {
        const newParams = new URLSearchParams(searchParams);
        newParams.set('tab', tab);
        setSearchParams(newParams);
    };
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
    const [hasProfile, setHasProfile] = useState(null); // null = loading, true, false
    const [buyerProfile, setBuyerProfile] = useState(null);
    const [isEditing, setIsEditing] = useState(false);
    const [updateLoading, setUpdateLoading] = useState(false);
    const [filterType, setFilterType] = useState('ALL'); // ALL, AUCTION, FIXED
    const [searchQuery, setSearchQuery] = useState('');
    const [profileMode, setProfileMode] = useState('view'); // view, edit
    const [wallet, setWallet] = useState(null);


    // My Orders Search/Filter State
    const [orderSearchQuery, setOrderSearchQuery] = useState('');
    const [orderStatusFilter, setOrderStatusFilter] = useState('ALL');
    const [orderDateFilter, setOrderDateFilter] = useState('');

    const fetchData = async () => {
        try {
            // Check buyer profile if we expect one or don't know yet
            if (user?.has_profile !== false) {
                try {
                    const profile = await buyerService.getProfile();
                    if (profile) {
                        setBuyerProfile(profile);
                        setHasProfile(true);
                    } else {
                        setHasProfile(false);
                    }
                } catch (err) {
                    // If 404, it means the user is a new buyer who hasn't filled the profile form yet
                    if (err.response?.status === 404) {
                        setHasProfile(false);
                    } else {
                        console.error("Error fetching buyer profile:", err);
                        setHasProfile(false);
                    }
                }
            } else {
                setHasProfile(false);
            }

            // Fetch wallet data
            try {
                const [walletData, transactionsData] = await Promise.all([
                    walletService.getWallet(),
                    walletService.getTransactions()
                ]);
                setWallet({ ...walletData, transactions: transactionsData });
            } catch (err) {
                console.error("Error fetching wallet:", err);
            }

            // Fetch marketplace listings (all active)
            const listingsData = await marketService.getListings({ status: 'ACTIVE' });
            setListings(listingsData);

            try {
                const bidsData = await marketService.getMyBids();
                setBids(bidsData);
            } catch {
                setBids([]);
            }

            // Fetch user's purchases
            try {
                const purchasesData = await marketService.getMyPurchases();
                setPurchases(purchasesData);
            } catch {
                setPurchases([]);
            }

            // Fetch user's wishlist
            try {
                const wishlistData = await marketService.getMyWishlist();
                setWishlist(wishlistData);
            } catch {
                setWishlist([]);
            }
        } catch (err) {
            console.error("Error fetching data:", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (!accessToken) {
            navigate('/login');
            return;
        }
        fetchData();
        const interval = setInterval(fetchData, 15000);
        return () => clearInterval(interval);
    }, [accessToken, navigate]);

    const handleUpdateProfile = async (e) => {
        e.preventDefault();
        setUpdateLoading(true);
        try {
            await buyerService.updateProfile(buyerProfile);
            setIsEditing(false);
            fetchData();
        } catch (err) {
            alert(err.response?.data?.detail || "Failed to update profile");
        } finally {
            setUpdateLoading(false);
        }
    };

    const handleLogout = async () => {
        await logout();
        navigate('/');
    };

    // Filter listings
    const filteredListings = listings.filter(l => {
        const matchesType = filterType === 'ALL' || l.price_type === filterType;
        const matchesSearch = !searchQuery || l.title.toLowerCase().includes(searchQuery.toLowerCase());
        return matchesType && matchesSearch;
    });

    const allMyBids = bids; // Show ALL participated auctions
    const wonBids = bids.filter(b => b.winner_status === 'PENDING' || b.winner_status === 'CONFIRMED' || b.winner_status === 'EXPIRED');

    const navItems = [
        { id: 'dashboard', label: 'Overview', icon: Home },
        { id: 'browse', label: 'Browse Products', icon: ShoppingCart },
        { id: 'orders', label: `My Orders (${purchases.length})`, icon: Package },
        { id: 'wishlist', label: `Wishlist (${wishlist.length})`, icon: Heart },
        { id: 'bids', label: `My Bids (${allMyBids.length})`, icon: Gavel },
        { id: 'won', label: `Won (${wonBids.length})`, icon: CheckCircle2 },
        { id: 'wallet', label: 'My Wallet', icon: History },
        { id: 'profile', label: 'My Profile', icon: UserCheck },
    ];

    // If profile doesn't exist yet, show onboarding
    if (hasProfile === false && activeTab !== 'browse') {
        // Auto-switch to profile tab for onboarding
    }

    return (
        <div className="min-h-screen bg-slate-50 flex flex-col lg:flex-row">
            <SEO title="Buyer Dashboard | CropManage" description="Browse and buy fresh produce directly from farmers" />

            {/* Sidebar - Desktop */}
            <aside className="hidden lg:flex w-80 bg-white border-r border-slate-100 flex-col p-8 sticky top-0 h-screen">
                <div className="flex items-center gap-4 mb-12 px-2">
                    <div className="bg-gradient-to-br from-blue-500 to-indigo-600 p-2.5 rounded-2xl shadow-lg shadow-blue-500/20">
                        <ShoppingBag size={24} className="text-white" />
                    </div>
                    <div>
                        <span className="text-xl font-bold text-slate-900 font-sans tracking-tight block leading-none">Buyer Hub</span>
                        <span className="text-[10px] text-slate-400 font-bold uppercase tracking-[0.2em] mt-1 block">Marketplace</span>
                    </div>
                </div>

                <nav className="flex-1 space-y-2">
                    {navItems.map(item => (
                        <button
                            key={item.id}
                            onClick={() => setActiveTab(item.id)}
                            className={`w-full flex items-center gap-4 p-4 rounded-2xl text-sm font-bold transition-all ${activeTab === item.id
                                ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white shadow-xl shadow-blue-500/20'
                                : 'text-slate-500 hover:bg-slate-50'
                                }`}
                        >
                            <item.icon size={20} /> {item.label}
                        </button>
                    ))}

                    <div className="h-px bg-slate-100 my-6 mx-2" />

                    {['farmer', 'seller'].includes(user?.role) && (
                        <Link
                            to={user.role === 'farmer' ? "/farmer-dashboard" : "/seller-dashboard"}
                            className="w-full flex items-center gap-4 p-4 rounded-2xl text-sm font-bold text-primary bg-primary/5 hover:bg-primary/10 transition-all border border-primary/10 group"
                        >
                            <UserCheck size={20} className="group-hover:scale-110 transition-transform" />
                            Switch to {user.role === 'farmer' ? "Farmer" : "Seller"} Studio
                        </Link>
                    )}

                    {hasProfile === false && (
                        <div className="p-4 rounded-2xl bg-amber-50 border border-amber-100 text-amber-700 text-xs font-bold">
                            <AlertCircle size={16} className="inline mr-2" />
                            Complete your profile to unlock all features
                        </div>
                    )}
                </nav>

                <button
                    onClick={handleLogout}
                    className="mt-auto flex items-center gap-4 p-4 rounded-2xl text-sm font-bold text-red-500 hover:bg-red-50 transition-all"
                >
                    <LogOut size={20} /> Logout
                </button>
            </aside>

            {/* Main Content */}
            <div className="flex-1 flex flex-col min-h-screen">
                {/* Header */}
                <header className="bg-white/80 backdrop-blur-md border-b border-slate-100 sticky top-0 z-30 px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <button onClick={() => setIsMobileMenuOpen(true)} className="lg:hidden p-2 text-slate-600">
                            <Menu size={24} />
                        </button>
                        <h1 className="text-xl font-black text-slate-900 uppercase tracking-tight">
                            {activeTab === 'dashboard' ? 'Overview' :
                                activeTab === 'browse' ? 'Marketplace' :
                                    activeTab === 'orders' ? 'My Orders' :
                                        activeTab === 'wishlist' ? 'My Wishlist' :
                                            activeTab === 'bids' ? 'My Active Bids' :
                                                activeTab === 'won' ? 'Auctions Won' :
                                                    activeTab === 'wallet' ? 'Wallet & Rewards' :
                                                        activeTab === 'notifications' ? 'Notifications History' : 'Buyer Profile'}
                        </h1>
                    </div>
                    <div className="flex items-center gap-6">
                        {wallet && (
                            <div className="hidden md:flex flex-col items-end px-4 border-r border-slate-100">
                                <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest leading-none mb-1">Non-Withdrawable</span>
                                <span className="text-sm font-black text-blue-600">₹{parseFloat(wallet.balance).toLocaleString()}</span>
                            </div>
                        )}
                        <NotificationBell />
                        {/* Profile Section Summary */}
                        <div className="flex items-center gap-4 pl-4 border-l border-slate-50">
                            <div className="hidden sm:flex flex-col items-end">
                                <p className="text-sm font-bold text-slate-900 leading-none flex items-center gap-1.5">
                                    {buyerProfile?.first_name || user?.name || 'Buyer'}
                                    {buyerProfile?.id_verified && <ShieldCheck size={14} className="text-emerald-500" />}
                                </p>
                                <p className="text-[10px] text-slate-400 font-bold mt-1 tracking-tight">{user.mobile_number}</p>
                            </div>

                            <div className="relative">
                                {(() => {
                                    let photoUrl = buyerProfile?.photo_url;
                                    if (photoUrl && photoUrl.length > 100 && !photoUrl.startsWith('data:')) {
                                        photoUrl = `data:image/jpeg;base64,${photoUrl}`;
                                    }
                                    return photoUrl ? (
                                        <div className="size-12 rounded-2xl border-2 border-white ring-4 ring-slate-50 bg-center bg-cover shadow-sm transition-all overflow-hidden" style={{ backgroundImage: `url(${photoUrl})` }} />
                                    ) : (
                                        <div className="size-12 rounded-2xl bg-white flex items-center justify-center border-2 border-slate-50 ring-4 ring-slate-50 text-blue-600 font-black shadow-sm">
                                            {(buyerProfile?.first_name?.[0] || user?.name?.[0] || 'B').toUpperCase()}
                                        </div>
                                    );
                                })()}
                                {buyerProfile?.id_verified && (
                                    <div className="absolute -bottom-1 -right-1 bg-emerald-500 text-white rounded-full p-0.5 border-2 border-white shadow-lg">
                                        <Check size={8} strokeWidth={4} />
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </header>

                <main className="p-6 md:p-10 max-w-7xl mx-auto w-full flex-1">
                    {loading ? (
                        <div className="text-center py-20">
                            <div className="animate-spin size-10 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4" />
                            <p className="text-slate-400 font-bold">Loading your dashboard...</p>
                        </div>
                    ) : (
                        <AnimatePresence mode="wait">
                            {activeTab === 'dashboard' && (
                                <motion.div key="overview" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="space-y-10">
                                    <div className="space-y-2">
                                        <div className="flex items-center gap-2 text-[10px] font-black text-blue-500 uppercase tracking-[0.3em]">
                                            <span className="size-2 bg-blue-500 rounded-full animate-pulse" />
                                            Buyer Command Active
                                        </div>
                                        <h1 className="text-4xl md:text-5xl font-black text-slate-950 tracking-tight">
                                            Hello, <span className="text-blue-600 italic">{buyerProfile?.first_name || user?.name?.split(' ')[0] || 'Buyer'}</span>
                                        </h1>
                                        <p className="text-slate-400 font-medium tracking-tight text-lg">Your marketplace dashboard is ready.</p>
                                    </div>

                                    {/* Stats Grid */}
                                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                                        <div className="bg-white p-8 rounded-[2.5rem] border border-slate-100 shadow-xl shadow-slate-900/5 hover:border-blue-300 transition-all cursor-pointer group" onClick={() => setActiveTab('orders')}>
                                            <div className="flex justify-between items-start mb-6">
                                                <div className="p-4 bg-blue-50 text-blue-600 rounded-2xl group-hover:scale-110 transition-transform">
                                                    <Package size={24} />
                                                </div>
                                            </div>
                                            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Total Purchases</p>
                                            <p className="text-3xl font-black tracking-tight">{purchases.length} <span className="text-sm font-bold text-slate-400">Orders</span></p>
                                        </div>

                                        <div className="bg-blue-600 p-8 rounded-[2.5rem] shadow-2xl shadow-blue-500/30 relative overflow-hidden text-white group cursor-pointer" onClick={() => setActiveTab('bids')}>
                                            <div className="absolute top-0 right-0 size-32 bg-white/20 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
                                            <div className="flex justify-between items-start mb-6 relative z-10">
                                                <div className="p-4 bg-white/10 text-white rounded-2xl backdrop-blur-md group-hover:scale-110 transition-transform">
                                                    <Gavel size={24} />
                                                </div>
                                            </div>
                                            <p className="text-[10px] font-black text-white/60 uppercase tracking-widest mb-1">Active Bids</p>
                                            <p className="text-3xl font-black tracking-tight">{allMyBids.length} <span className="text-sm font-bold text-white/60">Auctions</span></p>
                                            <div className="mt-4 text-[10px] font-black uppercase tracking-widest hover:underline flex items-center gap-1">
                                                View Details <ChevronRight size={12} />
                                            </div>
                                        </div>

                                        <div className="bg-white p-8 rounded-[2.5rem] border border-slate-100 shadow-xl shadow-slate-900/5 hover:border-rose-300 transition-all cursor-pointer group" onClick={() => setActiveTab('wishlist')}>
                                            <div className="flex justify-between items-start mb-6">
                                                <div className="p-4 bg-rose-50 text-rose-500 rounded-2xl group-hover:scale-110 transition-transform">
                                                    <Heart size={24} />
                                                </div>
                                            </div>
                                            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Wishlisted Items</p>
                                            <p className="text-3xl font-black tracking-tight">{wishlist.length} <span className="text-sm font-bold text-slate-400">Products</span></p>
                                        </div>
                                    </div>
                                </motion.div>
                            )}

                            {/* BROWSE TAB — Product Discovery */}
                            {activeTab === 'browse' && (
                                <motion.div key="browse" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                                    {/* Search & Filters */}
                                    <div className="flex flex-col sm:flex-row gap-4 mb-8">
                                        <div className="relative flex-1">
                                            <Search size={18} className="absolute left-5 top-1/2 -translate-y-1/2 text-slate-300" />
                                            <input
                                                type="text" placeholder="Search products..."
                                                value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
                                                className="w-full pl-14 pr-6 py-4 rounded-2xl bg-white border border-slate-100 text-sm font-bold text-slate-900 placeholder:text-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-300 shadow-sm"
                                            />
                                        </div>
                                        <div className="flex gap-2">
                                            {[
                                                { id: 'ALL', label: 'All', icon: Filter },
                                                { id: 'FIXED', label: 'Buy Now', icon: Tag },
                                                { id: 'AUCTION', label: 'Auctions', icon: Gavel },
                                            ].map(f => (
                                                <button key={f.id} onClick={() => setFilterType(f.id)}
                                                    className={`flex items-center gap-2 px-5 py-3 rounded-xl text-xs font-bold uppercase tracking-wider transition-all ${filterType === f.id ? 'bg-blue-500 text-white shadow-lg shadow-blue-500/20' : 'bg-white text-slate-400 border border-slate-100 hover:border-blue-200'
                                                        }`}>
                                                    <f.icon size={14} /> {f.label}
                                                </button>
                                            ))}
                                        </div>
                                    </div>

                                    {/* Product Grid */}
                                    {filteredListings.length === 0 ? (
                                        <div className="text-center py-24 bg-white rounded-[3rem] border border-slate-100">
                                            <ShoppingBag size={48} className="mx-auto text-slate-200 mb-6" />
                                            <h2 className="text-2xl font-bold text-slate-900 mb-2">No products found</h2>
                                            <p className="text-slate-400">Try adjusting your filters or check back later.</p>
                                        </div>
                                    ) : (
                                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                                            {filteredListings.map(listing => (
                                                <motion.div key={listing.id} layout
                                                    initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                                                    className="bg-white rounded-3xl border border-slate-100 shadow-lg shadow-slate-900/5 overflow-hidden group hover:shadow-2xl transition-all cursor-pointer"
                                                    onClick={() => navigate(`/marketplace/${listing.id}`)}
                                                >
                                                    <div className="h-44 bg-slate-50 overflow-hidden relative">
                                                        <img
                                                            src={listing.images?.[0] ? getMediaUrl(listing.images[0]) : 'https://images.unsplash.com/photo-1592982537447-7440770cbfc9?q=80&w=2045&auto=format&fit=crop'}
                                                            className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                                                            alt={listing.title}
                                                        />
                                                        <div className={`absolute top-4 right-4 px-3 py-1.5 rounded-xl text-[10px] font-black uppercase tracking-widest ${listing.price_type === 'AUCTION' ? 'bg-amber-500 text-white' : 'bg-emerald-500 text-white'}`}>
                                                            {listing.price_type === 'AUCTION' ? '🔥 Auction' : '💰 Buy Now'}
                                                        </div>
                                                    </div>
                                                    <div className="p-5 flex-1 flex flex-col justify-between">
                                                        <div>
                                                            <div className="flex items-center justify-between mb-2">
                                                                <div className="flex items-center gap-1.5 text-[9px] font-bold text-slate-400 uppercase">
                                                                    <Calendar size={10} />
                                                                    {new Date(listing.created_at).toLocaleString('en-IN', { day: 'numeric', month: 'short' })}
                                                                </div>
                                                                <div className="text-[8px] font-black text-slate-500 bg-slate-100 px-2 py-1 rounded-md uppercase tracking-tight border border-slate-200 shadow-sm">
                                                                    {listing.category?.name || listing.product?.category?.name || listing.custom_category_name || 'Agri Product'}
                                                                </div>
                                                            </div>
                                                            <h3 className="text-base font-black text-slate-900 truncate mb-0.5 tracking-tight">
                                                                {listing.product?.name || listing.custom_product_name || 'Agri Product'}
                                                            </h3>
                                                            <p className="text-[10px] font-bold text-slate-400 mb-4 line-clamp-1 italic uppercase tracking-wider">
                                                                {listing.title}
                                                            </p>
                                                        </div>

                                                        <div className="flex items-end justify-between pt-3 border-t border-slate-50">
                                                            <div>
                                                                <p className="text-[9px] font-bold text-slate-400 uppercase tracking-widest mb-0.5">
                                                                    {listing.price_type === 'AUCTION' ? 'Starting at' : 'Price'}
                                                                </p>
                                                                <p className="text-lg font-black text-slate-900">₹{Number(listing.base_price || listing.price).toLocaleString()}</p>
                                                            </div>
                                                            <div className="flex items-center gap-1.5 text-[10px] font-bold text-slate-400">
                                                                <Package size={14} className="text-blue-500" /> {listing.quantity} {listing.unit}
                                                            </div>
                                                        </div>
                                                        {listing.price_type === 'AUCTION' && listing.auction_end_time && (
                                                            <div className="mt-3 pt-3 border-t border-slate-50 text-[10px] font-bold">
                                                                <CountdownTimer endTime={listing.auction_end_time} />
                                                            </div>
                                                        )}
                                                    </div>
                                                </motion.div>
                                            ))}
                                        </div>
                                    )}
                                </motion.div>
                            )}


                            {activeTab === 'orders' && (
                                <motion.div key="orders" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-8">
                                    {/* Search and Filters Bar */}
                                    <div className="flex flex-col lg:flex-row gap-4 mb-4">
                                        <div className="relative flex-1 group">
                                            <Search size={18} className="absolute left-5 top-1/2 -translate-y-1/2 text-slate-300 group-focus-within:text-blue-500 transition-colors" />
                                            <input
                                                type="text"
                                                placeholder="Search orders by product name..."
                                                value={orderSearchQuery}
                                                onChange={(e) => setOrderSearchQuery(e.target.value)}
                                                className="w-full pl-14 pr-6 py-4 rounded-2xl bg-white border border-slate-100 text-sm font-bold text-slate-900 placeholder:text-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-300 shadow-sm transition-all"
                                            />
                                        </div>
                                        <div className="flex flex-wrap items-center gap-3">
                                            <div className="relative">
                                                <Filter size={14} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
                                                <select
                                                    value={orderStatusFilter}
                                                    onChange={(e) => setOrderStatusFilter(e.target.value)}
                                                    className="pl-10 pr-10 py-4 bg-white border border-slate-100 rounded-2xl text-xs font-black uppercase tracking-widest text-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/20 appearance-none shadow-sm cursor-pointer hover:border-blue-300 transition-all"
                                                >
                                                    <option value="ALL">All Status</option>
                                                    <option value="PAID">Paid</option>
                                                    <option value="ACCEPTED">Accepted</option>
                                                    <option value="PACKED">Packed</option>
                                                    <option value="SHIPPED">Shipped</option>
                                                    <option value="DELIVERED">Delivered</option>
                                                </select>
                                            </div>
                                            <div className="relative">
                                                <Calendar size={14} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
                                                <input
                                                    type="date"
                                                    value={orderDateFilter}
                                                    onChange={(e) => setOrderDateFilter(e.target.value)}
                                                    className="pl-10 pr-6 py-4 bg-white border border-slate-100 rounded-2xl text-xs font-black uppercase tracking-widest text-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/20 shadow-sm cursor-pointer hover:border-blue-300 transition-all"
                                                />
                                                {orderDateFilter && (
                                                    <button
                                                        onClick={() => setOrderDateFilter('')}
                                                        className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-red-500"
                                                    >
                                                        <X size={14} />
                                                    </button>
                                                )}
                                            </div>
                                        </div>
                                    </div>

                                    {(() => {
                                        const filteredPurchases = purchases.filter(o => {
                                            const matchesSearch = !orderSearchQuery || (o.title || '').toLowerCase().includes(orderSearchQuery.toLowerCase());
                                            const matchesStatus = orderStatusFilter === 'ALL' || o.status === orderStatusFilter;
                                            const matchesDate = !orderDateFilter || (o.purchase_date && o.purchase_date.split('T')[0] === orderDateFilter);
                                            return matchesSearch && matchesStatus && matchesDate;
                                        });

                                        if (filteredPurchases.length === 0) {
                                            return (
                                                <div className="text-center py-24 bg-white rounded-[3rem] border border-slate-100">
                                                    <Package size={48} className="mx-auto text-slate-200 mb-6" />
                                                    <h2 className="text-2xl font-bold text-slate-900 mb-2">
                                                        {purchases.length === 0 ? "No orders yet" : "No matching orders"}
                                                    </h2>
                                                    <p className="text-slate-400 mb-8">
                                                        {purchases.length === 0
                                                            ? "Items you purchase directly will appear here."
                                                            : "Try adjusting your search or filters."}
                                                    </p>
                                                    {purchases.length === 0 && (
                                                        <button onClick={() => setActiveTab('browse')} className="inline-flex items-center gap-2 px-8 py-4 bg-blue-500 text-white rounded-2xl font-bold shadow-xl shadow-blue-500/20">
                                                            Go Shopping <ChevronRight size={18} />
                                                        </button>
                                                    )}
                                                </div>
                                            );
                                        }

                                        return (
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                                {filteredPurchases.map(order => (
                                                    <PurchaseCard key={order.id} order={order} navigate={navigate} />
                                                ))}
                                            </div>
                                        );
                                    })()}
                                </motion.div>
                            )}

                            {/* WISHLIST TAB */}
                            {activeTab === 'wishlist' && (
                                <motion.div key="wishlist" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                                    {wishlist.length === 0 ? (
                                        <div className="text-center py-24 bg-white rounded-[3rem] border border-slate-100">
                                            <Heart size={48} className="mx-auto text-slate-200 mb-6" />
                                            <h2 className="text-2xl font-bold text-slate-900 mb-2">Your wishlist is empty</h2>
                                            <p className="text-slate-400">Products you save will appear here.</p>
                                        </div>
                                    ) : (
                                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                                            {wishlist.map(listing => (
                                                <motion.div key={listing.id} layout
                                                    initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
                                                    className="bg-white rounded-3xl border border-slate-100 shadow-lg shadow-slate-900/5 overflow-hidden group hover:shadow-2xl transition-all cursor-pointer"
                                                    onClick={() => navigate(`/marketplace/${listing.id}`)}
                                                >
                                                    <div className="h-44 bg-slate-50 overflow-hidden relative">
                                                        <img
                                                            src={listing.images?.[0] ? getMediaUrl(listing.images[0]) : 'https://images.unsplash.com/photo-1592982537447-7440770cbfc9?q=80&w=2045&auto=format&fit=crop'}
                                                            className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                                                            alt={listing.title}
                                                        />
                                                        <div className="absolute top-4 right-4">
                                                            <div className="p-2 bg-white/90 backdrop-blur-md rounded-xl text-red-500 shadow-sm">
                                                                <Heart size={16} fill="currentColor" />
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <div className="p-5">
                                                        <div className="flex items-center justify-between mb-2">
                                                            <div className="flex items-center gap-1.5 text-[9px] font-bold text-slate-400 uppercase">
                                                                <Calendar size={10} />
                                                                {new Date(listing.created_at).toLocaleString('en-IN', { day: 'numeric', month: 'short' })}
                                                            </div>
                                                            <div className="text-[8px] font-black text-slate-500 bg-slate-100 px-2 py-1 rounded-md uppercase tracking-tight border border-slate-200 shadow-sm">
                                                                {listing.category?.name || listing.product?.category?.name || listing.custom_category_name || 'Uncategorized'}
                                                            </div>
                                                        </div>

                                                        <h3 className="text-base font-black text-slate-900 truncate mb-0.5 tracking-tight">
                                                            {listing.product?.name || listing.custom_product_name || 'Agri Product'}
                                                        </h3>
                                                        <p className="text-[10px] font-bold text-slate-400 mb-3 line-clamp-1 italic uppercase tracking-wider">
                                                            {listing.title}
                                                        </p>

                                                        <div className="flex items-center justify-between pt-3 border-t border-slate-50">
                                                            <div>
                                                                <p className="text-lg font-black text-slate-900">₹{Number(listing.base_price || listing.price).toLocaleString()}</p>
                                                            </div>
                                                            <div className="flex items-center gap-1.5 text-[10px] font-bold text-slate-400">
                                                                <Package size={14} className="text-blue-500" /> {listing.quantity} {listing.unit}
                                                            </div>
                                                        </div>
                                                    </div>
                                                </motion.div>
                                            ))}
                                        </div>
                                    )}
                                </motion.div>
                            )}


                            {activeTab === 'bids' && (
                                <motion.div key="bids" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                                    {allMyBids.length === 0 ? (
                                        <div className="text-center py-24 bg-white rounded-[3rem] border border-slate-100">
                                            <Gavel size={48} className="mx-auto text-slate-200 mb-6" />
                                            <h2 className="text-2xl font-bold text-slate-900 mb-2">No active bids</h2>
                                            <p className="text-slate-400 mb-8">Browse the marketplace to find products and place bids!</p>
                                            <button onClick={() => setActiveTab('browse')} className="inline-flex items-center gap-2 px-8 py-4 bg-blue-500 text-white rounded-2xl font-bold shadow-xl shadow-blue-500/20">
                                                Browse Products <ChevronRight size={18} />
                                            </button>
                                        </div>
                                    ) : (
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                            {allMyBids.map(bid => (
                                                <BidCard key={bid.id} bid={bid} navigate={navigate} />
                                            ))}
                                        </div>
                                    )}
                                </motion.div>
                            )}

                            {/* WON TAB */}
                            {activeTab === 'won' && (
                                <motion.div key="won" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                                    {wonBids.length === 0 ? (
                                        <div className="text-center py-24 bg-white rounded-[3rem] border border-slate-100">
                                            <CheckCircle2 size={48} className="mx-auto text-slate-200 mb-6" />
                                            <h2 className="text-2xl font-bold text-slate-900 mb-2">No won auctions yet</h2>
                                            <p className="text-slate-400">Winning auctions will appear here.</p>
                                        </div>
                                    ) : (
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                            {wonBids.map(bid => (
                                                <BidCard key={bid.id} bid={bid} navigate={navigate} />
                                            ))}
                                        </div>
                                    )}
                                </motion.div>
                            )}

                            {/* WALLET TAB */}
                            {activeTab === 'wallet' && (
                                <motion.div key="wallet" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-8">
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                        {/* Wallet Card */}
                                        <div className="bg-gradient-to-br from-blue-600 to-indigo-700 rounded-[2.5rem] p-10 text-white shadow-2xl relative overflow-hidden group">
                                            <div className="absolute top-0 right-0 p-8 opacity-10 group-hover:scale-110 transition-transform duration-500">
                                                <History size={120} />
                                            </div>
                                            <div className="relative z-10">
                                                <p className="text-xs font-black uppercase tracking-[0.2em] opacity-80 mb-2">Total Reward Balance</p>
                                                <h2 className="text-5xl font-black mb-10 tracking-tighter">₹{wallet ? parseFloat(wallet.balance).toLocaleString() : '0'}</h2>
                                               
                                                <div className="flex flex-col gap-4">
                                                    <div className="bg-white/10 backdrop-blur-md rounded-2xl p-4 border border-white/10 flex items-center justify-between">
                                                        <span className="text-xs font-bold">Daily Reward Used</span>
                                                        <span className="text-xs font-black">₹{buyerProfile?.current_day_reward || '0.00'} / ₹500</span>
                                                    </div>
                                                    <div className="bg-amber-400/20 backdrop-blur-md rounded-2xl p-4 border border-amber-400/20 flex items-start gap-3">
                                                        <AlertCircle size={16} className="text-amber-300 mt-0.5" />
                                                        <p className="text-[10px] font-bold text-amber-50 leading-relaxed italic">
                                                            Rewards are non-withdrawable and can only be used for future auction participation fees.
                                                        </p>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        {/* Quick Info */}
                                        <div className="bg-white rounded-[2.5rem] border border-slate-100 p-8 shadow-xl flex flex-col justify-center">
                                            <h3 className="text-xl font-black text-slate-900 mb-6">How Rewards Work</h3>
                                            <div className="space-y-4">
                                                {[
                                                    { icon: CheckCircle2, text: "Participate in auctions with negative fees to earn rewards." },
                                                    { icon: Gavel, text: "You must place at least one valid bid to qualify for rewards." },
                                                    { icon: ShoppingBag, text: "Rewards are automatically credited when the auction ends." },
                                                    { icon: ShieldCheck, text: "Your daily limit is ₹500 to ensure fair distribution." },
                                                ].map((item, idx) => (
                                                    <div key={idx} className="flex gap-4 items-center">
                                                        <div className="size-8 rounded-xl bg-blue-50 text-blue-500 flex items-center justify-center shrink-0">
                                                            <item.icon size={16} />
                                                        </div>
                                                        <p className="text-xs font-bold text-slate-500">{item.text}</p>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    </div>

                                    {/* Transaction History */}
                                    <div className="bg-white rounded-[2.5rem] border border-slate-100 shadow-xl overflow-hidden">
                                        <div className="p-8 border-b border-slate-50">
                                            <h3 className="text-xl font-black text-slate-900">Transaction History</h3>
                                        </div>
                                       
                                        {!wallet?.transactions || wallet.transactions.length === 0 ? (
                                            <div className="p-20 text-center">
                                                <History size={48} className="mx-auto text-slate-100 mb-4" />
                                                <p className="text-slate-400 font-bold">No transactions recorded yet.</p>
                                            </div>
                                        ) : (
                                            <div className="overflow-x-auto">
                                                <table className="w-full text-left border-collapse">
                                                    <thead>
                                                        <tr className="bg-slate-50">
                                                            <th className="px-8 py-4 text-[10px] font-black text-slate-400 uppercase tracking-widest italic">Date</th>
                                                            <th className="px-8 py-4 text-[10px] font-black text-slate-400 uppercase tracking-widest italic">Description</th>
                                                            <th className="px-8 py-4 text-[10px] font-black text-slate-400 uppercase tracking-widest italic">Type</th>
                                                            <th className="px-8 py-4 text-[10px] font-black text-slate-400 uppercase tracking-widest italic text-right">Amount</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody className="divide-y divide-slate-50">
                                                        {wallet.transactions.sort((a,b) => new Date(b.created_at) - new Date(a.created_at)).map(tx => (
                                                            <tr key={tx.id} className="hover:bg-slate-50/50 transition-colors">
                                                                <td className="px-8 py-5 text-xs font-bold text-slate-500">
                                                                    {new Date(tx.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
                                                                </td>
                                                                <td className="px-8 py-5">
                                                                    <p className="text-xs font-black text-slate-900">{tx.description}</p>
                                                                    {tx.order_id && <p className="text-[10px] font-bold text-slate-400 mt-0.5 tracking-tighter uppercase italic">Order #{tx.order_id.slice(0,8)}</p>}
                                                                </td>
                                                                <td className="px-8 py-5">
                                                                    <span className={`px-3 py-1 rounded-full text-[9px] font-black uppercase tracking-widest ${tx.type === 'CREDIT' ? 'bg-emerald-50 text-emerald-600' : 'bg-red-50 text-red-600'}`}>
                                                                        {tx.type}
                                                                    </span>
                                                                </td>
                                                                <td className={`px-8 py-5 text-sm font-black text-right ${tx.type === 'CREDIT' ? 'text-emerald-600' : 'text-red-600'}`}>
                                                                    {tx.type === 'CREDIT' ? '+' : '-'} ₹{parseFloat(tx.amount).toLocaleString()}
                                                                </td>
                                                            </tr>
                                                        ))}
                                                    </tbody>
                                                </table>
                                            </div>
                                        )}
                                    </div>
                                </motion.div>
                            )}

                            {/* PROFILE TAB */}
                            {activeTab === 'profile' && (
                                <motion.div key="profile" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                                    {hasProfile === false || profileMode === 'edit' ? (
                                        <div className="max-w-4xl mx-auto">
                                            <div className="mb-8 flex items-center justify-between bg-white p-6 rounded-3xl border border-slate-100 shadow-sm">
                                                <div>
                                                    <h2 className="text-xl font-black text-slate-900">{hasProfile === false ? 'Setup Buyer Profile' : 'Update Profile'}</h2>
                                                    <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mt-1">Complete your identity and location details</p>
                                                </div>
                                                {hasProfile !== false && (
                                                    <button
                                                        onClick={() => setProfileMode('view')}
                                                        className="px-6 py-2 bg-slate-100 text-slate-600 rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-slate-200 transition-all"
                                                    >
                                                        Cancel
                                                    </button>
                                                )}
                                            </div>
                                        <BuyerProfileForm
                                            onComplete={() => {
                                                fetchData();
                                                setProfileMode('view');
                                                setActiveTab('dashboard');
                                            }}
                                            initialData={buyerProfile}
                                        />
                                        </div>
                                    ) : buyerProfile ? (
                                        <div className="max-w-4xl mx-auto space-y-8">
                                            {/* Rejection Notification Banner */}
                                            {buyerProfile.profile_status === 'Rejected' && (
                                                <motion.div
                                                    initial={{ opacity: 0, y: -20 }}
                                                    animate={{ opacity: 1, y: 0 }}
                                                    className="bg-red-50 border-2 border-red-100 rounded-[2.5rem] p-8 shadow-xl shadow-red-900/5 relative overflow-hidden group"
                                                >
                                                    <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                                                        <ShieldX size={80} />
                                                    </div>
                                                    <div className="flex flex-col md:flex-row items-start md:items-center gap-6 relative z-10">
                                                        <div className="size-16 bg-red-500 text-white rounded-2xl flex items-center justify-center shadow-lg shadow-red-500/20 shrink-0">
                                                            <XCircle size={32} />
                                                        </div>
                                                        <div className="flex-1">
                                                            <h3 className="text-xl font-black text-red-900 mb-1 leading-none">Application Rejected</h3>
                                                            <p className="text-xs font-bold text-red-400 uppercase tracking-widest mb-3">Please review and fix your profile</p>
                                                            <div className="bg-white/60 backdrop-blur-sm p-4 rounded-xl border border-red-100">
                                                                <p className="text-sm font-bold text-red-700 italic">"{buyerProfile.rejection_reason || 'No specific reason provided. Please ensure all documents are clear and valid.'}"</p>
                                                            </div>
                                                        </div>
                                                        <button
                                                            onClick={() => setProfileMode('edit')}
                                                            className="px-8 py-4 bg-red-600 text-white rounded-2xl font-black uppercase tracking-widest text-xs hover:bg-red-700 hover:scale-105 active:scale-95 transition-all shadow-xl shadow-red-600/20"
                                                        >
                                                            Fix Profile Now
                                                        </button>
                                                    </div>
                                                </motion.div>
                                            )}

                                            {/* Top Stat Cards */}
                                            <div className="max-w-2xl mx-auto">
                                                {/* Verification Card */}
                                                <div className={`rounded-[2.5rem] p-8 border-2 shadow-xl relative overflow-hidden flex flex-col justify-between ${buyerProfile.id_verified ? 'bg-emerald-50 border-emerald-100 text-emerald-900' : buyerProfile.profile_status === 'Rejected' ? 'bg-red-50 border-red-100 text-red-900' : 'bg-amber-50 border-amber-100 text-amber-900'}`}>
                                                    <div className="flex items-center justify-between mb-6">
                                                        <div className={`size-12 rounded-2xl flex items-center justify-center border ${buyerProfile.id_verified ? 'bg-emerald-500 text-white border-emerald-400' : buyerProfile.profile_status === 'Rejected' ? 'bg-red-500 text-white border-red-400' : 'bg-amber-500 text-white border-amber-400'}`}>
                                                            {buyerProfile.id_verified ? <ShieldCheck size={24} /> : buyerProfile.profile_status === 'Rejected' ? <ShieldX size={24} /> : <AlertCircle size={24} />}
                                                        </div>
                                                        <div className="flex flex-col items-end">
                                                            <span className="text-[10px] font-black uppercase tracking-widest opacity-60">Status</span>
                                                            <span className="text-xs font-black uppercase tracking-widest">{buyerProfile.id_verified ? 'Verified' : buyerProfile.profile_status === 'Rejected' ? 'Rejected' : 'Pending Verification'}</span>
                                                        </div>
                                                    </div>
                                                    <div>
                                                        <h4 className="text-lg font-black mb-2">{buyerProfile.id_verified ? 'Auction Access Active' : 'Basic Access Only'}</h4>
                                                        <p className="text-xs font-bold opacity-60 leading-relaxed mb-6">
                                                            {buyerProfile.id_verified
                                                                ? 'Your profile is fully verified. You can now participate in any live auction and place bids.'
                                                                : 'Complete your full KYC and selfie verification to participate in high-value auctions.'}
                                                        </p>

                                                    </div>
                                                </div>
                                            </div>

                                            {/* Profile Details View */}
                                            <div className="bg-white p-6 md:p-12 rounded-[2.5rem] border border-slate-100 shadow-xl shadow-slate-200/50">
                                                <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-12 pb-8 border-b border-slate-100">
                                                    <div>
                                                        <h1 className="text-3xl md:text-5xl text-blue-600 mb-2 tracking-tight">Buyer Profile</h1>
                                                        <p className="text-sm md:text-lg text-slate-500">Professional procurement and identity details</p>
                                                    </div>
                                                    <button
                                                        onClick={() => setProfileMode('edit')}
                                                        className="w-full md:w-auto bg-blue-600 text-white py-4 px-8 rounded-2xl flex items-center justify-center gap-2 shadow-lg shadow-blue-200 hover:scale-[1.02] transition-transform"
                                                    >
                                                        <UserCheck size={20} /> Update Profile
                                                    </button>
                                                </div>

                                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-10">
                                                    {/* Identity Card */}
                                                    <div className="bg-slate-50/50 p-8 rounded-[2.5rem] border border-slate-100">
                                                        <div className="flex items-center gap-4 mb-8">
                                                            <div className="bg-white p-3 rounded-2xl shadow-sm text-blue-500"><User size={20} /></div>
                                                            <h3 className="text-lg font-bold text-slate-900">Identity Details</h3>
                                                        </div>
                                                        <div className="space-y-6">
                                                            <ProfileDetailItem label="Full Name" value={`${buyerProfile.first_name} ${buyerProfile.middle_name || ''} ${buyerProfile.last_name}`} />
                                                            <div className="grid grid-cols-2 gap-4">
                                                                <ProfileDetailItem label="Age" value={buyerProfile.age ? `${buyerProfile.age} Years` : 'N/A'} />
                                                                <ProfileDetailItem label="Gender" value={buyerProfile.gender} />
                                                            </div>
                                                            <ProfileDetailItem label="Identity Proof" value={`${buyerProfile.id_type} (•••• ${buyerProfile.id_number?.slice(-4) || 'XXXX'})`} />
                                                        </div>
                                                    </div>

                                                    {/* Location Card */}
                                                    <div className="bg-slate-50/50 p-8 rounded-[2.5rem] border border-slate-100">
                                                        <div className="flex items-center gap-4 mb-8">
                                                            <div className="bg-white p-3 rounded-2xl shadow-sm text-blue-500"><MapPin size={20} /></div>
                                                            <h3 className="text-lg font-bold text-slate-900">Location Context</h3>
                                                        </div>
                                                        <div className="space-y-6">
                                                            <ProfileDetailItem label="Delivery Address" value={buyerProfile.address} />
                                                            <div className="grid grid-cols-2 gap-4">
                                                                <ProfileDetailItem label="Village" value={buyerProfile.village} />
                                                                <ProfileDetailItem label="Pincode" value={buyerProfile.pincode} />
                                                            </div>
                                                            <ProfileDetailItem label="Region" value={`${buyerProfile.district}, ${buyerProfile.state}`} />
                                                        </div>
                                                    </div>

                                                    {/* Preferences Card */}
                                                    <div className="bg-slate-50/50 p-8 rounded-[2.5rem] border border-slate-100">
                                                        <div className="flex items-center gap-4 mb-8">
                                                            <div className="bg-white p-3 rounded-2xl shadow-sm text-blue-500"><Tag size={20} /></div>
                                                            <h3 className="text-lg font-bold text-slate-900">Preferences</h3>
                                                        </div>
                                                        <div className="space-y-6">
                                                            <ProfileDetailItem label="Education" value={buyerProfile.education_level} />
                                                            <ProfileDetailItem label="Preferred Language" value={buyerProfile.preferred_language} />
                                                            <ProfileDetailItem label="Mobile Number" value={buyerProfile.mobile_number} />
                                                            <div className="pt-4 border-t border-slate-200/60 mt-2">
                                                                <div className="flex items-center justify-between p-3 bg-white rounded-xl shadow-sm">
                                                                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">KYC Status</span>
                                                                    <span className={`text-[10px] font-black px-2 py-1 rounded-md ${buyerProfile.id_verified ? 'bg-emerald-100 text-emerald-600' : 'bg-amber-100 text-amber-600'}`}>
                                                                        {buyerProfile.id_verified ? 'VERIFIED' : 'PENDING'}
                                                                    </span>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>

                                                {buyerProfile.id_verified && (
                                                    <div className="mt-12 p-8 rounded-[2rem] bg-blue-600 text-white relative overflow-hidden shadow-xl shadow-blue-200">
                                                        <div className="absolute top-0 right-0 size-32 bg-white/10 rounded-full blur-2xl -translate-y-1/2 translate-x-1/2" />
                                                        <div className="relative z-10 flex flex-col md:flex-row items-center gap-6 text-center md:text-left">
                                                            <div className="bg-white/20 p-4 rounded-3xl backdrop-blur-md">
                                                                <ShieldCheck size={32} />
                                                            </div>
                                                            <div>
                                                                <h4 className="text-xl font-bold mb-1">Identity Verified</h4>
                                                                <p className="text-blue-100 text-sm font-medium">Your profile is locked for security as it has been verified by the administration team.</p>
                                                            </div>
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="text-center py-20">
                                            <div className="animate-spin size-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto" />
                                        </div>
                                    )}
                                </motion.div>
                            )}
                            {activeTab === 'notifications' && (
                                <motion.div
                                    key="notifications-view"
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, y: -10 }}
                                >
                                    <NotificationsView />
                                </motion.div>
                            )}
                        </AnimatePresence>
                    )}
                </main>
            </div >

            {/* Mobile Nav Overlay */}
            < AnimatePresence >
                {isMobileMenuOpen && (
                    <div className="fixed inset-0 z-[100] lg:hidden">
                        <motion.div
                            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                            className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm"
                            onClick={() => setIsMobileMenuOpen(false)}
                        />
                        <motion.div
                            className="absolute left-0 top-0 bottom-0 w-80 bg-white shadow-2xl flex flex-col p-8"
                            initial={{ x: '-100%' }} animate={{ x: 0 }} exit={{ x: '-100%' }}
                            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                        >
                            <div className="flex items-center justify-between mb-12">
                                <div className="flex items-center gap-4">
                                    <div className="bg-gradient-to-br from-blue-500 to-indigo-600 p-2.5 rounded-2xl shadow-lg">
                                        <ShoppingBag size={24} className="text-white" />
                                    </div>
                                    <span className="text-xl font-bold text-slate-900">Buyer Hub</span>
                                </div>
                                <button onClick={() => setIsMobileMenuOpen(false)} className="p-3 text-slate-400 bg-slate-50 rounded-2xl">
                                    <X size={28} />
                                </button>
                            </div>

                            <div className="flex-1 space-y-2">
                                {navItems.map(item => (
                                    <button
                                        key={item.id}
                                        className={`w-full flex items-center gap-5 p-5 rounded-3xl text-lg font-bold transition-all ${activeTab === item.id
                                            ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white shadow-xl'
                                            : 'text-slate-500 hover:bg-slate-50'
                                            }`}
                                        onClick={() => { setActiveTab(item.id); setIsMobileMenuOpen(false); }}
                                    >
                                        <item.icon size={26} /> {item.label}
                                    </button>
                                ))}

                                {['farmer', 'seller'].includes(user?.role) && (
                                    <Link
                                        to={user.role === 'farmer' ? "/farmer-dashboard" : "/seller-dashboard"}
                                        className="w-full flex items-center gap-5 p-5 rounded-3xl text-lg font-bold text-primary bg-primary/5 border border-primary/10 mt-4"
                                        onClick={() => setIsMobileMenuOpen(false)}
                                    >
                                        <UserCheck size={26} className="mr-5" /> Switch to {user.role === 'farmer' ? "Farmer" : "Seller"} Studio
                                    </Link>
                                )}
                            </div>

                            <div className="pt-8 mt-4 border-t border-slate-100">
                                <button
                                    onClick={handleLogout}
                                    className="w-full bg-red-50 text-red-500 p-6 rounded-[2rem] flex items-center justify-center gap-3 text-lg font-bold hover:bg-red-100 transition-colors"
                                >
                                    <LogOut size={24} /> Logout
                                </button>
                            </div>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence >
        </div >
    );
};

// Helper Components
const ProfileDetailItem = ({ label, value }) => (
    <div className="space-y-1.5">
        <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block pl-0.5">
            {label}
        </label>
        <div className="text-base text-slate-900 font-bold leading-tight px-0.5 break-words">
            {value || <span className="text-stone-300 italic font-medium">Pending Update</span>}
        </div>
    </div>
);



const BidCard = ({ bid, navigate }) => {
    const getStatusUI = () => {
        if (bid.status === 'ACTIVE') {
            return bid.user_is_winning
                ? { label: '🟢 Winning', className: 'bg-emerald-50 text-emerald-500' }
                : { label: '🟡 Outbid', className: 'bg-amber-50 text-amber-500' };
        }

        switch (bid.winner_status) {
            case 'CONFIRMED':
                return { label: '✅ Order Confirmed', className: 'bg-emerald-500 text-white' };
            case 'PENDING':
                return { label: '🎉 Won! Action Required', className: 'bg-blue-500 text-white animate-pulse' };
            case 'AWAITING_SELLER_REQUEST':
                return { label: '🏆 Won (Waiting for seller)', className: 'bg-blue-50 text-blue-500' };
            case 'EXPIRED':
                return { label: '❌ Not Accepted (Expired)', className: 'bg-red-50 text-red-500' };
            case 'LOST':
                return { label: '💀 Auction Ended (Lost)', className: 'bg-slate-100 text-slate-400' };
            default:
                return { label: 'Ended', className: 'bg-slate-100 text-slate-400' };
        }
    };

    const statusUI = getStatusUI();

    return (
        <motion.div
            layout initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-[2rem] border border-slate-100 shadow-xl shadow-slate-900/5 overflow-hidden group hover:shadow-2xl transition-all"
        >
            <div className="flex p-5 gap-5">
                <div className="w-28 h-28 rounded-2xl overflow-hidden bg-slate-50 shrink-0 border border-slate-100 relative">
                    <img
                        src={bid.images?.[0] ? getMediaUrl(bid.images[0]) : 'https://images.unsplash.com/photo-1592982537447-7440770cbfc9?q=80&w=2045&auto=format&fit=crop'}
                        className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                        alt={bid.title}
                    />
                    {bid.user_is_winning && bid.status === 'ACTIVE' && (
                        <div className="absolute inset-0 bg-emerald-500/10 flex items-center justify-center backdrop-blur-[2px]">
                            <span className="text-[10px] font-black text-emerald-600 bg-white px-2 py-0.5 rounded-full shadow-sm">WINNING</span>
                        </div>
                    )}
                </div>
                <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-1.5 text-[9px] font-bold text-slate-400 uppercase">
                            <Calendar size={10} />
                            {bid.last_bid_at ? new Date(bid.last_bid_at).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', hour12: true }) : 'N/A'}
                        </div>
                        <div className="text-[8px] font-black text-slate-500 bg-slate-100 px-2 py-1 rounded-md uppercase tracking-tight border border-slate-200 shadow-sm">
                            {bid.category?.name || bid.product?.category?.name || bid.custom_category_name || 'Uncategorized'}
                        </div>
                    </div>

                    <h3 className="text-lg font-black text-slate-950 truncate tracking-tight mb-0.5">
                        {bid.product?.name || bid.custom_product_name || 'Agri Product'}
                    </h3>
                    <p className="text-[10px] font-bold text-slate-400 line-clamp-1 italic uppercase tracking-wider mb-2">
                        {bid.title}
                    </p>
                   
                    <div className="flex items-center justify-between">
                        <div className={`px-2 py-1 rounded-lg text-[8px] font-black uppercase tracking-widest ${statusUI.className}`}>
                            {statusUI.label}
                        </div>
                    </div>

                    {/* Detailed Message based on winner_status */}
                    <div className="mt-2 text-[9px] font-bold leading-relaxed">
                        {bid.winner_status === 'PENDING' && (
                            <div className="text-blue-600 bg-blue-50 px-2 py-1 rounded-lg">
                                {bid.winner_rank > 1
                                    ? `Previous winner expired. You (Rank ${bid.winner_rank}) are now eligible! Confirm within ${bid.confirmation_timeout_minutes || 5} mins.`
                                    : `Congratulations! Please confirm your win within ${bid.confirmation_timeout_minutes || 5} minutes!`
                                }
                            </div>
                        )}
                        {bid.winner_status === 'EXPIRED' && (
                            <div className="text-red-600 bg-red-50 px-2 py-1 rounded-lg">
                                {bid.winner_rank === 1 ? "You didn't confirm in time. Bid passed to next winner." : "Confirmation period expired."}
                            </div>
                        )}
                        {bid.winner_status === 'LOST' && (
                            <div className="text-slate-400">
                                You were outbid or not selected as winner.
                            </div>
                        )}
                    </div>
                </div>
            </div>
            <div className="px-5 py-3 bg-slate-50/50 border-t border-slate-100 flex items-center justify-between">
                <div>
                    <p className="text-[9px] font-bold text-slate-400 uppercase tracking-widest">Your Bid</p>
                    <p className="text-base font-black text-slate-900">₹{Number(bid.your_highest_bid).toLocaleString()}</p>
                </div>
                <div className="flex items-center gap-3 text-[10px] font-bold text-slate-400 uppercase">
                    <Package size={14} className="text-blue-500" /> {bid.quantity} {bid.unit}
                    {bid.status === 'ACTIVE' && bid.auction_end_time && (
                        <CountdownTimer endTime={bid.auction_end_time} />
                    )}
                </div>
                <button
                    onClick={(e) => { e.stopPropagation(); navigate(`/marketplace/${bid.listing_id || bid.id}`); }}
                    className={`px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest border transition-all shadow-sm ${bid.winner_status === 'PENDING'
                        ? 'bg-blue-600 text-white border-blue-600 hover:bg-blue-700'
                        : 'bg-white text-slate-900 border-slate-200 hover:bg-slate-900 hover:text-white hover:border-slate-900'
                        }`}
                >
                    {bid.winner_status === 'PENDING' ? 'Confirm Now' : 'View'}
                </button>
            </div>
        </motion.div>
    );
};

// Reusable Purchase Card Component
const PurchaseCard = ({ order, navigate }) => (
    <motion.div
        layout initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
        className="bg-white rounded-[2rem] border border-slate-100 shadow-xl shadow-slate-900/5 overflow-hidden group hover:shadow-2xl transition-all"
    >
        <div className="flex p-5 gap-5">
            <div className="w-28 h-28 rounded-2xl overflow-hidden bg-slate-50 shrink-0 border border-slate-100 relative">
                <img
                    src={order.images?.[0] ? getMediaUrl(order.images[0]) : 'https://images.unsplash.com/photo-1592982537447-7440770cbfc9?q=80&w=2045&auto=format&fit=crop'}
                    className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                    alt={order.title}
                />
            </div>
            <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-1.5 text-[9px] font-bold text-slate-400 uppercase">
                        <Calendar size={10} />
                        {new Date(order.purchase_date).toLocaleString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
                    </div>
                    <div className="text-[8px] font-black text-slate-500 bg-slate-100 px-2 py-1 rounded-md uppercase tracking-tight border border-slate-200 shadow-sm">
                        {order.category?.name || order.product?.category?.name || order.custom_category_name || 'Uncategorized'}
                    </div>
                </div>

                <h3 className="text-lg font-black text-slate-950 truncate tracking-tight mb-0.5">
                    {order.product?.name || order.custom_product_name || 'Agri Product'}
                </h3>
                <p className="text-[10px] font-bold text-slate-400 line-clamp-1 italic uppercase tracking-wider mb-2">
                    {order.title}
                </p>

                <div className="flex items-center gap-2">
                    <div className="px-2 py-1 rounded-lg text-[8px] font-black uppercase tracking-widest bg-emerald-500 text-white flex items-center gap-1">
                        <CheckCircle2 size={10} /> PURCHASED
                    </div>
                </div>
            </div>
        </div>
        <div className="px-5 py-3 bg-slate-50/50 border-t border-slate-100 flex items-center justify-between">
            <div>
                <p className="text-[9px] font-bold text-slate-400 uppercase tracking-widest">Price Paid</p>
                <p className="text-base font-black text-slate-900">₹{Number(order.amount_paid).toLocaleString()}</p>
            </div>
            <div className="flex items-center gap-3 text-[10px] font-bold text-slate-400 uppercase">
                <Package size={14} className="text-blue-500" /> {order.quantity} {order.unit}
            </div>
            <button
                onClick={(e) => {
                    e.stopPropagation();
                    const cleanOrderId = order.id?.replace('order-', '');
                    navigate(`/marketplace/${order.listing_id}?order_id=${cleanOrderId}`);
                }}
                className="px-4 py-2 bg-white text-slate-900 rounded-xl text-[10px] font-black uppercase tracking-widest border border-slate-200 hover:bg-slate-900 hover:text-white hover:border-slate-900 transition-all shadow-sm"
            >
                View Details
            </button>
        </div>
    </motion.div>
);

export default BuyerDashboard;