import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    User, MapPin, Shield,
    Camera, Upload, ChevronRight, ChevronLeft,
    Check, Info, Search, X, FileText,
    AlertCircle, ShieldCheck, FileCheck, ShieldAlert,
    Loader2, ScanFace, LocateFixed, Navigation
} from 'lucide-react';
import { useSearchParams } from 'react-router-dom';
import buyerService from '../../services/buyer';
import { locationData } from '../../services/locationData';
import { useAuth } from '../../context/AuthContext';

const BuyerProfileForm = ({ onComplete, initialData }) => {
    const [searchParams, setSearchParams] = useSearchParams();
    const { user: authUser } = useAuth();

    // Sections logic - move inside to use formData/initialData
    const activeSections = [
        { id: 1, title: 'Personal Info', icon: User },
        { id: 2, title: 'Location', icon: MapPin },
        { id: 3, title: 'KYC & ID', icon: Shield },
        // Only show Face Check if not already verified
        ...(!initialData?.photo_verified ? [{ id: 4, title: 'Face Check', icon: Camera }] : [])
    ];
    
    const maxSteps = activeSections.length;

    // Step persistence
    const currentStep = parseInt(searchParams.get('step')) || 1;
    const setCurrentStep = (step) => {
        const newParams = new URLSearchParams(searchParams);
        newParams.set('step', step);
        setSearchParams(newParams);
    };

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    // Face verification state
    const [uploadedPhoto, setUploadedPhoto] = useState(null);   // file input
    const [cameraPhoto, setCameraPhoto] = useState(null);       // live camera
    const [faceMatch, setFaceMatch] = useState(null);           // { matched, score } | null
    const [faceChecking, setFaceChecking] = useState(false);

    // Pincode detection state
    const [pincodeLoading, setPincodeLoading] = useState(false);
    const [detectedVillages, setDetectedVillages] = useState([]);
    const [districtData, setDistrictData] = useState([]);
    const [showPincodeSuggestions, setShowPincodeSuggestions] = useState(false);

    // Helper to convert dataURL to File object
    const dataURLtoFile = (dataurl, filename) => {
        let arr = dataurl.split(','), mime = arr[0].match(/:(.*?);/)[1],
            bstr = atob(arr[1]), n = bstr.length, u8arr = new Uint8Array(n);
        while (n--) { u8arr[n] = bstr.charCodeAt(n); }
        return new File([u8arr], filename, { type: mime });
    };

    // Face verification logic
    useEffect(() => {
        if (!uploadedPhoto || !cameraPhoto) return;
        const checkFaces = async () => {
            setFaceChecking(true);
            setFaceMatch(null);
            try {
                const photoFile = dataURLtoFile(uploadedPhoto, 'photo.jpg');
                const selfieFile = dataURLtoFile(cameraPhoto, 'selfie.jpg');

                // Backend expects: (photo: UploadFile, selfie: UploadFile)
                const res = await buyerService.verifyFace(photoFile, selfieFile);
                const data = res; // services/buyer already returns response.data

                if (data.status === 'Error') {
                    setFaceMatch({
                        matched: false,
                        confidence: '0%',
                        status: 'Error',
                        noFace: data.no_face,
                        errorMsg: data.error_msg ?? 'Face check failed.',
                    });
                    return;
                }

                const matched = data.matched === true;
                const confidence = data.confidence ?? '0%';
                const status = data.status ?? (matched ? 'Match' : 'No Match');
                setFaceMatch({ matched, confidence, status, distance: data.distance });
                setFormData(prev => ({ ...prev, photo_verified: matched }));
            } catch (err) {
                setFaceMatch({ matched: false, confidence: '0%', status: 'Error', errorMsg: 'Face verification failed.' });
            } finally {
                setFaceChecking(false);
            }
        };
        checkFaces();
    }, [uploadedPhoto, cameraPhoto]);

    // Auto-clear error
    useEffect(() => {
        if (error) {
            const timer = setTimeout(() => setError(''), 5000);
            return () => clearTimeout(timer);
        }
    }, [error]);

    // Sync formData if initialData changes (e.g. loaded after mount)
    useEffect(() => {
        if (initialData) {
            let processedIDDoc = initialData.id_document_url;
            if (processedIDDoc && processedIDDoc.length > 500 && !processedIDDoc.startsWith('data:')) {
                processedIDDoc = `data:image/jpeg;base64,${processedIDDoc}`;
            }

            let processedPhoto = initialData.photo_url;
            if (processedPhoto && processedPhoto.length > 500 && !processedPhoto.startsWith('data:')) {
                processedPhoto = `data:image/jpeg;base64,${processedPhoto}`;
            }

            setFormData(prev => ({
                ...prev,
                ...initialData,
                photo_url: processedPhoto,
                id_document_url: processedIDDoc,
                date_of_birth: initialData.date_of_birth ? new Date(initialData.date_of_birth).toISOString().split('T')[0] : prev.date_of_birth,
            }));

            if (processedPhoto) setUploadedPhoto(processedPhoto);
        }
    }, [initialData]);

    const [formData, setFormData] = useState(() => {
        if (initialData) {
            return {
                ...initialData,
                date_of_birth: initialData.date_of_birth ? new Date(initialData.date_of_birth).toISOString().split('T')[0] : '',
            };
        }

        const draftKey = authUser?.user_id ? `buyer_profile_draft_${authUser.user_id}` : 'buyer_profile_draft';
        const savedDraft = localStorage.getItem(draftKey);
        if (savedDraft) {
            try {
                const draft = JSON.parse(savedDraft);
                if (authUser?.mobile_number && (!draft.mobile_number || draft.mobile_number !== authUser.mobile_number)) {
                    draft.mobile_number = authUser.mobile_number;
                }
                return draft;
            } catch (e) {
                console.error("Failed to parse saved draft", e);
            }
        }

        return {
            first_name: '',
            middle_name: '',
            last_name: '',
            gender: 'Male',
            mobile_number: authUser?.mobile_number || '',
            education_level: '',
            preferred_language: 'English',
            date_of_birth: '',
            photo_url: '',
            camera_capture_url: '',
            photo_verified: false,
            country: '',
            state: '',
            district: '',
            village: '',
            pincode: '',
            latitude: '',
            longitude: '',
            address: '',
            id_type: 'National ID/Aadhar',
            id_number: '',
            id_document_url: ''
        };
    });

    // Sync to localStorage
    useEffect(() => {
        if (!initialData && authUser?.user_id) {
            try {
                // Exclude large base64 strings to prevent QuotaExceededError
                const { photo_url, id_document_url, camera_capture_url, ...textData } = formData;
                localStorage.setItem(`buyer_profile_draft_${authUser.user_id}`, JSON.stringify(textData));
            } catch (e) {
                console.warn("Could not save profile draft (storage full):", e);
            }
        }
    }, [formData, initialData, authUser?.user_id]);

    const handleInputChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value
        }));
    };

    const isVerified = initialData?.id_verified === true;
    const VERIFIED_LOCKED_FIELDS = [
        'first_name', 'middle_name', 'last_name',
        'date_of_birth', 'gender',
        'id_type', 'id_number', 'id_document_url',
        'photo_url'
    ];

    const isLocked = (fieldName) => {
        if (fieldName === 'mobile_number') return true;
        if (isVerified) return VERIFIED_LOCKED_FIELDS.includes(fieldName);
        return false;
    };

    const validateCurrentStep = () => {
        if (currentStep === 1) {
            if (!formData.first_name?.trim() || formData.first_name.trim().length < 2)
                return "First name must be at least 2 characters";
            if (!formData.last_name?.trim() || formData.last_name.trim().length < 1)
                return "Last name is required";
            if (!formData.date_of_birth)
                return "Please select your Date of Birth";

            const dob = new Date(formData.date_of_birth);
            const today = new Date();
            let age = today.getFullYear() - dob.getFullYear();
            const m = today.getMonth() - dob.getMonth();
            if (m < 0 || (m === 0 && today.getDate() < dob.getDate())) {
                age--;
            }
            if (age < 18) {
                return "Buyers must be at least 18 years old to register.";
            }

            if (!formData.education_level) return "Please select your education level";
            if (!formData.preferred_language) return "Please select your preferred language";
        }
        if (currentStep === 2) {
            if (!formData.country) return "Please select a country";
            if (!formData.state) return "Please select a state";
            if (!formData.district) return "Please select a district";
            if (!formData.pincode || formData.pincode.length < 4 || formData.pincode.length > 10)
                return "Please enter a valid pincode (4-10 characters)";
            if (!formData.village?.trim()) return "Please enter your village/area";
            if (!formData.address?.trim()) return "Please enter your full address";
        }
        if (currentStep === 3) {
            if (!formData.id_type) return "Please select an ID type";
            if (!formData.id_number?.trim()) return "Please enter your ID number";
            if (!formData.id_document_url) return "Please upload your ID document image";

            if (formData.id_type === 'Aadhaar' && !/^\d{12}$/.test(formData.id_number))
                return "Aadhaar must be exactly 12 numeric digits";
        }
        if (currentStep === 4) {
            if (formData.photo_verified) return null; // Already verified, can proceed or submit
            if (!uploadedPhoto) return "Please upload your photo";
            if (!cameraPhoto) return "Please capture a live camera photo";
            if (faceChecking) return "Face verification in progress...";
            if (!faceMatch || !faceMatch.matched) return "Face verification failed. Please ensure both photos match.";
        }
        return null;
    };

    const handleNext = () => {
        const stepError = validateCurrentStep();
        if (stepError) {
            setError(stepError);
            return;
        }
        if (currentStep < maxSteps) setCurrentStep(currentStep + 1);
    };

    const handleBack = () => {
        if (currentStep > 1) setCurrentStep(currentStep - 1);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        const stepError = validateCurrentStep();
        if (stepError) {
            setError(stepError);
            return;
        }

        setLoading(true);
        setError('');
        try {
            const payload = {
                ...formData,
                date_of_birth: formData.date_of_birth ? new Date(formData.date_of_birth).toISOString() : null,
                latitude: formData.latitude ? parseFloat(formData.latitude) : null,
                longitude: formData.longitude ? parseFloat(formData.longitude) : null
            };

            await (initialData ? buyerService.updateProfile(payload) : buyerService.createProfile(payload));

            localStorage.removeItem(`buyer_profile_draft_${authUser?.user_id}`);
            onComplete && onComplete();
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to save profile');
        } finally {
            setLoading(false);
        }
    };

    const renderStep = () => {
        switch (currentStep) {
            case 1:
                return (
                    <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-10">
                        <div>
                            <h3 className="text-xl font-bold text-slate-900 mb-1 flex items-center gap-2">
                                <User className="text-blue-600" size={24} /> Personal Identity
                            </h3>
                            <p className="text-slate-500 text-sm">Essential details for your buyer account.</p>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
                            <div className="md:col-span-4 space-y-2">
                                <label className="text-xs font-bold text-slate-400 uppercase tracking-widest ml-1">First Name</label>
                                <input type="text" name="first_name" value={formData.first_name || ''} onChange={handleInputChange} readOnly={isLocked('first_name')} className="input-field" placeholder="John" />
                            </div>
                            <div className="md:col-span-4 space-y-2">
                                <label className="text-xs font-bold text-slate-400 uppercase tracking-widest ml-1">Middle Name</label>
                                <input type="text" name="middle_name" value={formData.middle_name || ''} onChange={handleInputChange} readOnly={isLocked('middle_name')} className="input-field" placeholder="Optional" />
                            </div>
                            <div className="md:col-span-4 space-y-2">
                                <label className="text-xs font-bold text-slate-400 uppercase tracking-widest ml-1">Last Name</label>
                                <input type="text" name="last_name" value={formData.last_name || ''} onChange={handleInputChange} readOnly={isLocked('last_name')} className="input-field" placeholder="Doe" />
                            </div>

                            <div className="md:col-span-6 space-y-2">
                                <label className="text-xs font-bold text-slate-400 uppercase tracking-widest ml-1">Date of Birth</label>
                                <input
                                    type="date" name="date_of_birth" value={formData.date_of_birth || ''} onChange={handleInputChange}
                                    readOnly={isLocked('date_of_birth')} className="input-field"
                                    max={new Date(new Date().setFullYear(new Date().getFullYear() - 18)).toISOString().split('T')[0]}
                                />
                            </div>
                            <div className="md:col-span-6 space-y-2">
                                <label className="text-xs font-bold text-slate-400 uppercase tracking-widest ml-1">Gender</label>
                                <div className="relative">
                                    <select name="gender" value={formData.gender || 'Male'} onChange={handleInputChange} disabled={isLocked('gender')} className="input-field appearance-none">
                                        <option value="Male">Male</option>
                                        <option value="Female">Female</option>
                                        <option value="Other">Other</option>
                                    </select>
                                    <ChevronRight size={20} className="absolute right-5 top-1/2 -translate-y-1/2 rotate-90 text-slate-400 pointer-events-none" />
                                </div>
                            </div>

                            <div className="md:col-span-4 space-y-2 opacity-60">
                                <label className="text-xs font-bold text-slate-400 uppercase tracking-widest ml-1">Mobile (Linked)</label>
                                <input type="text" value={formData.mobile_number || ''} readOnly className="input-field bg-slate-50" />
                            </div>
                            <div className="md:col-span-4 space-y-2">
                                <label className="text-xs font-bold text-slate-400 uppercase tracking-widest ml-1">Education</label>
                                <div className="relative">
                                    <select name="education_level" value={formData.education_level || ''} onChange={handleInputChange} className="input-field appearance-none">
                                        <option value="">Select Education Level</option>
                                        <option>No Formal Education</option>
                                        <option>Primary Education</option>
                                        <option>Secondary School</option>
                                        <option>Undergraduate Degree</option>
                                        <option>Postgraduate Degree</option>
                                        <option>Other</option>
                                    </select>
                                    <ChevronRight size={20} className="absolute right-5 top-1/2 -translate-y-1/2 rotate-90 text-slate-400 pointer-events-none" />
                                </div>
                            </div>
                            <div className="md:col-span-4 space-y-2">
                                <label className="text-xs font-bold text-slate-400 uppercase tracking-widest ml-1">Language</label>
                                <div className="relative">
                                    <select name="preferred_language" value={formData.preferred_language || 'English'} onChange={handleInputChange} className="input-field appearance-none">
                                        {['English', 'Hindi', 'Telugu', 'Tamil', 'Kannada', 'Malayalam', 'Marathi'].map(l => <option key={l} value={l}>{l}</option>)}
                                    </select>
                                    <ChevronRight size={20} className="absolute right-5 top-1/2 -translate-y-1/2 rotate-90 text-slate-400 pointer-events-none" />
                                </div>
                            </div>
                        </div>
                    </motion.div>
                );
            case 2:
                const allCountries = locationData.getAllCountries();
                const states = formData.country ? locationData.getStatesByCountry(allCountries.find(c => c.name === formData.country)?.isoCode) : [];
                const districts = (formData.country && formData.state) ? locationData.getDistrictsByState(
                    allCountries.find(c => c.name === formData.country)?.isoCode,
                    states.find(s => s.name === formData.state)?.isoCode
                ) : [];

                return (
                    <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-10">
                        <div>
                            <h3 className="text-xl font-bold text-slate-900 mb-1 flex items-center gap-2">
                                <LocateFixed className="text-blue-600" size={24} /> Regional & Delivery Details
                            </h3>
                            <p className="text-slate-500 text-sm">Define your primary delivery location and contact specifications.</p>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            <div className="space-y-2">
                                <label className="text-xs font-bold text-slate-400 uppercase tracking-widest ml-1">Country</label>
                                <div className="relative">
                                    <select
                                        name="country" value={formData.country || ''}
                                        onChange={(e) => {
                                            const country = e.target.value;
                                            setFormData(prev => ({ ...prev, country, state: '', district: '', pincode: '', village: '' }));
                                        }} required className="input-field appearance-none"
                                    >
                                        <option value="">Select Country</option>
                                        {allCountries.map(c => <option key={c.isoCode} value={c.name}>{c.name}</option>)}
                                    </select>
                                    <ChevronRight size={20} className="absolute right-5 top-1/2 -translate-y-1/2 rotate-90 text-slate-400 pointer-events-none" />
                                </div>
                            </div>
                            <div className="space-y-2">
                                <label className="text-xs font-bold text-slate-400 uppercase tracking-widest ml-1">State / Province</label>
                                <div className="relative">
                                    <select
                                        name="state" value={formData.state || ''}
                                        onChange={(e) => {
                                            const state = e.target.value;
                                            setFormData(prev => ({ ...prev, state, district: '', pincode: '', village: '' }));
                                        }} required disabled={!formData.country} className="input-field appearance-none"
                                    >
                                        <option value="">Select State</option>
                                        {states.map(s => <option key={s.isoCode} value={s.name}>{s.name}</option>)}
                                    </select>
                                    <ChevronRight size={20} className="absolute right-5 top-1/2 -translate-y-1/2 rotate-90 text-slate-400 pointer-events-none" />
                                </div>
                            </div>
                            <div className="space-y-2">
                                <label className="text-xs font-bold text-slate-400 uppercase tracking-widest ml-1">District / City</label>
                                <div className="relative">
                                    <select
                                        name="district" value={formData.district || ''}
                                        onChange={async (e) => {
                                            const districtName = e.target.value;
                                            setDistrictData([]);
                                            setDetectedVillages([]);
                                            setFormData(prev => ({ ...prev, district: districtName, pincode: '', village: '' }));

                                            if (districtName) {
                                                setPincodeLoading(true);
                                                try {
                                                    const res = await fetch(`https://api.postalpincode.in/postoffice/${districtName}`);
                                                    const data = await res.json();
                                                    if (data[0].Status === 'Success') setDistrictData(data[0].PostOffice);
                                                } catch (err) { } finally { setPincodeLoading(false); }
                                            }
                                        }} required disabled={!formData.state} className="input-field appearance-none"
                                    >
                                        <option value="">Select District</option>
                                        {districts.map(d => <option key={d} value={d}>{d}</option>)}
                                    </select>
                                    <ChevronRight size={20} className="absolute right-5 top-1/2 -translate-y-1/2 rotate-90 text-slate-400 pointer-events-none" />
                                </div>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="space-y-2 relative">
                                <label className="text-xs font-bold text-slate-400 uppercase tracking-widest ml-1">Pincode</label>
                                <div className="relative">
                                    <input
                                        type="text" name="pincode" value={formData.pincode || ''} maxLength="10"
                                        onChange={async (e) => {
                                            const val = e.target.value.trim();
                                            setFormData(prev => ({ ...prev, pincode: val, village: '' }));
                                            setShowPincodeSuggestions(true);

                                            if (val.length >= 4 && formData.country) {
                                                setPincodeLoading(true);
                                                try {
                                                    const data = await locationData.lookupPincode(formData.country, val);
                                                    if (data && data.places) {
                                                        const pos = data.places;
                                                        setDistrictData(pos);
                                                        setDetectedVillages(pos.map(p => p['place name']));

                                                        const first = pos[0];
                                                        setFormData(prev => {
                                                            const updates = { pincode: val };
                                                            // Auto-fill state and district if available and currently empty or different
                                                            if (!prev.state || prev.state === '') updates.state = first.state;
                                                            if (!prev.district || prev.district === '') updates.district = first.district;

                                                            // Precision: if city/place name is unique, auto-select it
                                                            if (pos.length === 1) {
                                                                updates.village = first['place name'];
                                                            }

                                                            // Update Lat/Long if available
                                                            if (first.latitude && first.longitude) {
                                                                updates.latitude = parseFloat(first.latitude);
                                                                updates.longitude = parseFloat(first.longitude);
                                                            }

                                                            return { ...prev, ...updates };
                                                        });
                                                    }
                                                } catch (err) { } finally { setPincodeLoading(false); }
                                            }
                                        }}
                                        onFocus={() => setShowPincodeSuggestions(true)}
                                        onBlur={() => setTimeout(() => setShowPincodeSuggestions(false), 200)}
                                        className="input-field" placeholder="Enter postal code"
                                    />
                                    {pincodeLoading && <div className="absolute right-4 top-1/2 -translate-y-1/2"><Loader2 className="animate-spin text-blue-600" size={20} /></div>}
                                    {showPincodeSuggestions && districtData.length > 0 && !pincodeLoading && (
                                        <div className="absolute z-50 left-0 right-0 top-full mt-2 bg-white rounded-2xl shadow-2xl border border-slate-100 max-h-48 overflow-y-auto custom-scrollbar">
                                            {detectedVillages.map((village, idx) => (
                                                <button
                                                    key={`${village}-${idx}`} type="button" onClick={() => {
                                                        const place = districtData[idx];
                                                        setFormData(prev => ({
                                                            ...prev,
                                                            village: village,
                                                            latitude: place.latitude ? parseFloat(place.latitude) : prev.latitude,
                                                            longitude: place.longitude ? parseFloat(place.longitude) : prev.longitude
                                                        }));
                                                        setShowPincodeSuggestions(false);
                                                    }} className="w-full text-left px-5 py-3 hover:bg-slate-50 text-sm font-medium text-slate-700 transition-colors flex items-center justify-between border-b border-slate-50 last:border-0"
                                                >
                                                    <span>{village}</span>
                                                    <span className="text-[10px] text-slate-400 uppercase tracking-widest bg-slate-100 px-2 py-0.5 rounded-full">Suggested Area</span>
                                                </button>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            </div>
                            <div className="space-y-2">
                                <label className="text-xs font-bold text-slate-400 uppercase tracking-widest ml-1">Village / Town</label>
                                <div className="relative">
                                    {detectedVillages.length > 0 ? (
                                        <select
                                            name="village"
                                            value={formData.village || ''}
                                            onChange={handleInputChange}
                                            className="input-field appearance-none border-blue-600/30"
                                        >
                                            <option value="">Select Village/Area</option>
                                            {detectedVillages.map(v => <option key={v} value={v}>{v}</option>)}
                                        </select>
                                    ) : (
                                        <input
                                            type="text"
                                            name="village"
                                            value={formData.village || ''}
                                            onChange={handleInputChange}
                                            className="input-field"
                                            placeholder="Enter village/town name"
                                        />
                                    )}
                                    {detectedVillages.length > 0 && <ChevronRight size={20} className="absolute right-5 top-1/2 -translate-y-1/2 rotate-90 text-slate-400 pointer-events-none" />}
                                </div>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="text-xs font-bold text-slate-400 uppercase tracking-widest ml-1">Full Address</label>
                            <textarea name="address" value={formData.address || ''} onChange={handleInputChange} rows={3} placeholder="House no, Street, Landmark..." className="w-full px-6 py-4 rounded-2xl bg-slate-50 border border-transparent text-sm font-bold text-slate-900 focus:bg-white focus:border-blue-500 transition-all outline-none resize-none" />
                        </div>

                        <div className="bg-slate-50 border border-slate-100 rounded-[2.5rem] p-8 space-y-6">
                            <div className="flex flex-col md:flex-row justify-between gap-4">
                                <div>
                                    <h4 className="text-slate-900 font-bold mb-1">Geospatial Coordinates</h4>
                                    <p className="text-slate-500 text-xs">Precisely locate your delivery point via satellite GPS.</p>
                                </div>
                                <button type="button" onClick={() => {
                                    if (navigator.geolocation) {
                                        navigator.geolocation.getCurrentPosition(p => setFormData(v => ({ ...v, latitude: p.coords.latitude, longitude: p.coords.longitude })));
                                    }
                                }} className="px-8 py-3 rounded-2xl bg-white border border-slate-100 text-blue-600 font-bold text-sm hover:bg-blue-600 hover:text-white hover:border-blue-600 transition-all flex items-center justify-center gap-2 shadow-sm"><Navigation size={18} /> Update From current GPS</button>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div className="space-y-2"><label className="text-[10px] font-bold text-slate-400 uppercase ml-1">Latitude</label><input type="text" value={formData.latitude || ''} readOnly className="input-field bg-white/50" /></div>
                                <div className="space-y-2"><label className="text-[10px] font-bold text-slate-400 uppercase ml-1">Longitude</label><input type="text" value={formData.longitude || ''} readOnly className="input-field bg-white/50" /></div>
                            </div>
                        </div>
                    </motion.div>
                );
            case 3:
                return (
                    <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-10">
                        <div>
                            <h3 className="text-xl font-bold text-slate-900 mb-1 flex items-center gap-2">
                                <ShieldCheck className="text-blue-600" size={24} /> KYC Verification
                            </h3>
                            <p className="text-slate-500 text-sm">Required for high-value auction participation.</p>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                            <div className="space-y-4">
                                <div className="space-y-2">
                                    <label className="text-xs font-bold text-slate-400 uppercase tracking-widest ml-1">ID Type</label>
                                    <div className="relative">
                                        <select name="id_type" value={formData.id_type || ''} onChange={handleInputChange} disabled={isLocked('id_type')} className="input-field appearance-none">
                                            <option value="">Select ID Type</option>
                                            {['Aadhaar', 'Passport', 'Voter ID', 'National ID', 'PAN Card'].map(t => <option key={t} value={t}>{t}</option>)}
                                        </select>
                                        <ChevronRight size={20} className="absolute right-5 top-1/2 -translate-y-1/2 rotate-90 text-slate-400 pointer-events-none" />
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <label className="text-xs font-bold text-slate-400 uppercase tracking-widest ml-1">Document Number</label>
                                    <input type="text" name="id_number" value={formData.id_number || ''} onChange={handleInputChange} readOnly={isLocked('id_number')} className="input-field" placeholder="Enter ID number" />
                                </div>
                            </div>

                            <div className="space-y-4">
                                <label className="text-xs font-bold text-slate-400 uppercase tracking-widest ml-1">ID Document Upload</label>
                                <div
                                    className={`aspect-video rounded-3xl border-2 border-dashed flex flex-col items-center justify-center cursor-pointer overflow-hidden transition-all group ${formData.id_document_url ? 'border-blue-600 bg-white shadow-xl' : 'border-slate-200 bg-slate-50 hover:border-blue-300'}`}
                                    onClick={() => !isLocked('id_document_url') && document.getElementById('id-upload').click()}
                                    style={formData.id_document_url ? { backgroundImage: `url(${formData.id_document_url})`, backgroundSize: 'cover', backgroundPosition: 'center' } : {}}
                                >
                                    {!formData.id_document_url && (
                                        <div className="text-center p-6">
                                            <div className="bg-white p-4 rounded-2xl mb-3 text-slate-400 group-hover:text-blue-600 transition-colors inline-block"><Upload size={24} /></div>
                                            <p className="text-slate-900 font-bold text-sm">Click to Upload ID</p>
                                        </div>
                                    )}
                                    <input type="file" id="id-upload" hidden accept="image/*" onChange={(e) => {
                                        const file = e.target.files[0];
                                        if (file) {
                                            const reader = new FileReader();
                                            reader.onload = (ev) => setFormData(p => ({ ...p, id_document_url: ev.target.result }));
                                            reader.readAsDataURL(file);
                                        }
                                    }} />
                                </div>
                            </div>
                        </div>
                    </motion.div>
                );
            case 4:
                return (
                    <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-10">
                        <div>
                            <h3 className="text-xl font-bold text-slate-900 mb-1 flex items-center gap-2">
                                <ScanFace className="text-blue-600" size={24} /> Biometric Check
                            </h3>
                            <p className="text-slate-500 text-sm">Final step to verify your live presence.</p>
                        </div>

                        {formData.photo_verified ? (
                            <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="bg-emerald-50 border-2 border-emerald-100 rounded-[2.5rem] p-10 text-center space-y-6">
                                <div className="size-24 bg-emerald-500 text-white rounded-full flex items-center justify-center mx-auto shadow-xl shadow-emerald-500/20">
                                    <ShieldCheck size={48} />
                                </div>
                                <div>
                                    <h4 className="text-2xl font-black text-emerald-900 mb-2">Biometrics Verified</h4>
                                    <p className="text-emerald-700/60 font-bold text-sm max-w-sm mx-auto">Your face verification is already completed and securely stored in our system. No further action is required.</p>
                                </div>
                                <div className="flex justify-center gap-4">
                                    <div className="px-6 py-3 bg-white rounded-2xl border border-emerald-100 text-emerald-600 text-xs font-black uppercase tracking-widest shadow-sm">
                                        Identity Secure
                                    </div>
                                </div>
                            </motion.div>
                        ) : (
                            <>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 bg-slate-50 p-8 rounded-[2.5rem]">
                                    <div className="space-y-4">
                                        <label className="text-xs font-bold text-slate-400 uppercase tracking-widest">Buyer Photo</label>
                                        <div
                                            className={`aspect-square rounded-3xl border-2 border-dashed flex items-center justify-center cursor-pointer transition-all ${uploadedPhoto ? 'border-blue-600' : 'border-slate-200 bg-white'}`}
                                            onClick={() => document.getElementById('face-photo').click()}
                                            style={uploadedPhoto ? { backgroundImage: `url(${uploadedPhoto})`, backgroundSize: 'cover' } : {}}
                                        >
                                            {!uploadedPhoto && <Upload className="text-slate-300" />}
                                            <input type="file" id="face-photo" hidden accept="image/*" onChange={(e) => {
                                                const file = e.target.files[0];
                                                if (file) {
                                                    const reader = new FileReader();
                                                    reader.onload = (ev) => { setUploadedPhoto(ev.target.result); setFormData(p => ({ ...p, photo_url: ev.target.result })); setFaceMatch(null); };
                                                    reader.readAsDataURL(file);
                                                }
                                            }} />
                                        </div>
                                    </div>
                                    <div className="space-y-4">
                                        <label className="text-xs font-bold text-slate-400 uppercase tracking-widest">Live Capture</label>
                                        <CameraCapture
                                            onCapture={url => { setCameraPhoto(url); setFormData(p => ({ ...p, camera_capture_url: url })); setFaceMatch(null); }}
                                            capturedUrl={cameraPhoto}
                                        />
                                    </div>
                                </div>

                                <AnimatePresence mode="wait">
                                    {faceChecking && (
                                        <motion.div className="flex items-center gap-4 bg-blue-50 border border-blue-100 rounded-2xl p-4">
                                            <Loader2 className="animate-spin text-blue-600" />
                                            <p className="text-blue-900 font-bold text-sm">Matching Biometrics...</p>
                                        </motion.div>
                                    )}
                                    {faceMatch && (
                                        <motion.div className={`flex items-center gap-4 border rounded-[2rem] p-5 ${faceMatch.matched ? 'bg-emerald-50 border-emerald-100' : 'bg-red-50 border-red-100'}`}>
                                            <div className={`size-12 rounded-2xl flex items-center justify-center text-white ${faceMatch.matched ? 'bg-emerald-600' : 'bg-red-600'}`}>
                                                {faceMatch.matched ? <Check /> : <AlertCircle />}
                                            </div>
                                            <div>
                                                <p className="font-bold text-sm">{faceMatch.matched ? 'Identity Verified' : 'Check Mismatch'}</p>
                                                <p className="text-xs opacity-70">{faceMatch.matched ? 'Biometric data match confirmed.' : 'Faces do not match. Please retake.'}</p>
                                            </div>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </>
                        )}
                    </motion.div>
                );
            default: return null;
        }
    };

    return (
        <div className="max-w-5xl mx-auto px-6 py-12">
            <div className="flex justify-between items-center mb-16 px-4">
                {activeSections.map((s, idx) => (
                    <div key={s.id} className="flex flex-col items-center">
                        <button
                            type="button"
                            onClick={() => currentStep > (idx + 1) && setCurrentStep(idx + 1)}
                            className={`size-12 rounded-2xl flex items-center justify-center transition-all ${currentStep >= (idx + 1) ? 'bg-blue-600 text-white shadow-xl' : 'bg-white text-slate-400 border-2'}`}
                        >
                            {currentStep > (idx + 1) ? <Check size={20} /> : <s.icon size={20} />}
                        </button>
                        <span className={`mt-3 text-[10px] font-bold uppercase tracking-widest ${currentStep >= (idx + 1) ? 'text-slate-900' : 'text-slate-400'}`}>{s.title}</span>
                    </div>
                ))}
            </div>

            <div className="bg-white rounded-[3.5rem] shadow-2xl p-8 md:p-14 border border-slate-100">
                <form onSubmit={handleSubmit} className="space-y-12">
                    <AnimatePresence mode="wait">{renderStep()}</AnimatePresence>

                    <div className="flex flex-col md:flex-row gap-6 pt-10 border-t items-center justify-between">
                        {currentStep > 1 && (
                            <button type="button" onClick={handleBack} className="w-full md:w-auto px-8 py-4 rounded-2xl border-2 text-slate-400 font-bold flex items-center gap-2 hover:bg-slate-50 transition-all"><ChevronLeft /> Back</button>
                        )}
                        <div className="w-full md:flex-1">
                            {currentStep < maxSteps ? (
                                <button type="button" onClick={handleNext} className="w-full py-4 rounded-2xl bg-blue-600 text-white font-bold shadow-lg hover:scale-[1.01] transition-all flex items-center justify-center gap-2">Next Step <ChevronRight /></button>
                            ) : (
                                <button type="submit" disabled={loading} className="w-full py-4 rounded-2xl bg-slate-900 text-white font-bold shadow-lg hover:scale-[1.01] transition-all flex items-center justify-center gap-2 disabled:bg-slate-300">
                                    {loading ? <Loader2 className="animate-spin" /> : <>Complete Profile <Check /></>}
                                </button>
                            )}
                        </div>
                    </div>
                </form>
            </div>

            {error && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm">
                    <motion.div initial={{ scale: 0.9 }} animate={{ scale: 1 }} className="bg-white p-8 rounded-3xl max-w-sm w-full shadow-2xl border-2 border-red-50">
                        <div className="size-16 bg-red-50 rounded-2xl flex items-center justify-center mb-6 text-red-500"><AlertCircle size={32} /></div>
                        <h3 className="text-xl font-bold mb-2">Error</h3>
                        <p className="text-slate-500 mb-6">{error}</p>
                        <button onClick={() => setError('')} className="w-full py-4 bg-slate-900 text-white rounded-xl font-bold">Close</button>
                    </motion.div>
                </div>
            )}
        </div>
    );
};

const CameraCapture = ({ onCapture, capturedUrl }) => {
    const [stream, setStream] = useState(null);
    const videoRef = useRef(null);
    const canvasRef = useRef(null);

    const startCamera = async () => {
        try {
            const s = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' } });
            setStream(s);
            setTimeout(() => { if (videoRef.current) videoRef.current.srcObject = s; }, 50);
        } catch (err) { alert("Camera access denied"); }
    };

    const capture = () => {
        const video = videoRef.current;
        const canvas = canvasRef.current;
        if (video && canvas) {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            canvas.getContext('2d').drawImage(video, 0, 0);
            onCapture(canvas.toDataURL('image/jpeg', 0.95));
            stopCamera();
        }
    };

    const stopCamera = () => { if (stream) { stream.getTracks().forEach(t => t.stop()); setStream(null); } };

    return (
        <>
            <div className="aspect-square rounded-3xl bg-slate-50 border-2 border-dashed relative overflow-hidden group flex flex-col items-center justify-center">
                {capturedUrl ? (
                    <div className="w-full h-full bg-cover bg-center" style={{ backgroundImage: `url(${capturedUrl})` }}>
                        <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                            <button type="button" onClick={startCamera} className="bg-white px-4 py-2 rounded-xl font-bold text-xs shadow-xl">Retake</button>
                        </div>
                    </div>
                ) : (
                    <button type="button" onClick={startCamera} className="flex flex-col items-center gap-2 text-blue-600"><Camera /><span className="text-xs font-bold">Open Camera</span></button>
                )}
                <canvas ref={canvasRef} className="hidden" />
            </div>

            <AnimatePresence>
                {stream && (
                    <div className="fixed inset-0 z-[200] bg-black/80 flex items-center justify-center p-4">
                        <div className="bg-slate-900 rounded-3xl overflow-hidden w-full max-w-md">
                            <video ref={videoRef} autoPlay playsInline muted className="w-full aspect-square object-cover" style={{ transform: 'scaleX(-1)' }} />
                            <div className="p-6 flex flex-col gap-4">
                                <button type="button" onClick={capture} className="w-full py-4 bg-blue-600 text-white rounded-2xl font-bold shadow-lg shadow-blue-600/20">Capture Photo</button>
                                <button type="button" onClick={stopCamera} className="text-slate-400 text-sm">Cancel</button>
                            </div>
                        </div>
                    </div>
                )}
            </AnimatePresence>
        </>
    );
};

export default BuyerProfileForm;