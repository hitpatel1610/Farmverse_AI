import React, { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useNavigate } from 'react-router-dom'
import { FiUser, FiPhone, FiMail, FiMapPin, FiHome, FiLock } from 'react-icons/fi'
import FormContainer from '../../components/common/FormContainer'
import Input from '../../components/common/Input'
import Select from '../../components/common/Select'
import Button from '../../components/common/Button'
import Toast from '../../components/common/Toast'

// List of all 33 districts of Gujarat
const GUJARAT_DISTRICTS = [
    'Ahmedabad', 'Amreli', 'Anand', 'Aravalli', 'Banaskantha', 'Bharuch', 'Bhavnagar',
    'Botad', 'Chhota Udepur', 'Dahod', 'Devbhumi Dwarka', 'Gandhinagar', 'Gir Somnath',
    'Jamnagar', 'Junagadh', 'Kheda', 'Kutch', 'Mahisagar', 'Mehsana', 'Morbi', 'Narmada',
    'Navsari', 'Panchmahal', 'Patan', 'Porbandar', 'Rajkot', 'Sabarkantha', 'Surat',
    'Surendranagar', 'Tapi', 'The Dangs', 'Vadodara', 'Valsad'
]

import { authAPI } from '../../services/api'

export const FarmerRegister = () => {
    const navigate = useNavigate()
    const [isLoading, setIsLoading] = useState(false)
    const [toast, setToast] = useState(null)
    const triggerToast = (msg, type = 'error') => setToast({ message: msg, type })

    const getErrorMessage = (err) => {
        if (!err.response) return 'Network error: Please check your connection'
        if (err.response.status === 401) return 'Unauthorized: Please check credentials'
        if (err.response.status === 404) return 'No data found'
        if (err.response.status >= 500) return 'Server error: Please try again later'

        const errorData = err.response.data
        let errorMsg = errorData?.message || errorData?.errors?.non_field_errors?.[0] || errorData?.errors?.error
        if (!errorMsg && errorData?.errors) {
            const fields = Object.keys(errorData.errors)
            if (fields.length > 0) {
                const firstField = fields[0]
                const firstMsg = errorData.errors[firstField]
                errorMsg = `${firstField}: ${Array.isArray(firstMsg) ? firstMsg[0] : firstMsg}`
            }
        }
        return errorMsg || 'રજીસ્ટ્રેશન નિષ્ફળ ગયું છે'
    }

    const {
        register,
        handleSubmit,
        watch,
        formState: { errors }
    } = useForm({
        defaultValues: {
            fullName: '',
            mobile: '',
            email: '',
            village: '',
            taluka: '',
            district: '',
            state: 'Gujarat',
            password: '',
            confirmPassword: '',
            acceptTerms: false
        }
    })

    // Watch password field to check compatibility in Confirm Password validation
    const password = watch('password')

    const onSubmit = async (data) => {
        if (isLoading) return;
        setIsLoading(true)
        try {
            const res = await authAPI.register({
                full_name: data.fullName,
                mobile: data.mobile,
                email: data.email,
                password: data.password,
                role: 'Farmer'
            })
            if (res.success) {
                triggerToast(res.message || 'રજીસ્ટ્રેશન સફળ રહ્યું છે! કૃપા કરીને લોગિન કરો.', 'success')
                setTimeout(() => navigate('/farmer/login'), 2000)
            } else {
                triggerToast(res.message || 'રજીસ્ટ્રેશન નિષ્ફળ રહ્યું', 'error')
            }
        } catch (err) {
            console.error(err)
            triggerToast(getErrorMessage(err), 'error')
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <FormContainer
            title="ખેડૂત રજીસ્ટ્રેશન" // "Farmer Registration" in Gujarati
            subtitle="નવું ખાતું બનાવવા માટે માહિતી ભરો" // "Fill info to create a new account"
            roleTheme="farmer"
            backTo="/farmer/login"
            backLabel="લોગિન પર પાછા જાઓ"
        >
            {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                {/* Full Name */}
                <Input
                    label="પૂરું નામ (Full Name)"
                    name="fullName"
                    placeholder="તમારું પૂરું નામ દાખલ કરો"
                    icon={FiUser}
                    required
                    error={errors.fullName}
                    {...register('fullName', { required: 'પૂરું નામ લખવું ફરજિયાત છે' })}
                />

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Mobile Number */}
                    <Input
                        label="મોબાઈલ નંબર (Mobile)"
                        name="mobile"
                        type="tel"
                        placeholder="૧૦ આંકડાનો નંબર"
                        icon={FiPhone}
                        required
                        error={errors.mobile}
                        {...register('mobile', {
                            required: 'મોબાઈલ નંબર ફરજિયાત છે',
                            pattern: {
                                value: /^[6-9]\d{9}$/,
                                message: 'કૃપા કરીને ૧૦ અંકનો માન્ય નંબર લખો'
                            }
                        })}
                    />

                    {/* Email */}
                    <Input
                        label="ઈમેલ આઈડી (Email)"
                        name="email"
                        type="email"
                        placeholder="દા.ત. name@domain.com"
                        icon={FiMail}
                        required
                        error={errors.email}
                        {...register('email', {
                            required: 'ઈમેલ આઈડી ફરજિયાત છે',
                            pattern: {
                                value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                                message: 'કૃપા કરીને યોગ્ય ઈમેલ આઈડી દાખલ કરો'
                            }
                        })}
                    />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Village */}
                    <Input
                        label="ગામ (Village)"
                        name="village"
                        placeholder="ગામનું નામ"
                        icon={FiHome}
                        required
                        error={errors.village}
                        {...register('village', { required: 'ગામનું નામ ફરજિયાત છે' })}
                    />

                    {/* Taluka */}
                    <Input
                        label="તાલુકો (Taluka)"
                        name="taluka"
                        placeholder="તાલુકાનું નામ"
                        icon={FiMapPin}
                        required
                        error={errors.taluka}
                        {...register('taluka', { required: 'તાલુકો ફરજિયાત છે' })}
                    />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Select
                        label="જિલ્લો (District)"
                        name="district"
                        icon={FiMapPin}
                        required
                        error={errors.district}
                        {...register('district', { required: 'જિલ્લો પસંદ કરવો ફરજિયાત છે' })}
                    >
                        <option value="">જિલ્લો પસંદ કરો</option>
                        {GUJARAT_DISTRICTS.map((dst) => (
                            <option key={dst} value={dst}>{dst}</option>
                        ))}
                    </Select>

                    {/* State (Default Gujarat) */}
                    <Input
                        label="રાજ્ય (State)"
                        name="state"
                        placeholder="Gujarat"
                        icon={FiMapPin}
                        disabled
                        required
                        {...register('state')}
                    />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Password */}
                    <Input
                        label="પાસવર્ડ (Password)"
                        name="password"
                        type="password"
                        placeholder="પીન અથવા ગુપ્ત કોડ"
                        icon={FiLock}
                        required
                        error={errors.password}
                        {...register('password', {
                            required: 'પાસવર્ડ ફરજિયાત છે',
                            pattern: {
                                value: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/,
                                message: 'પાસવર્ડમાં ઓછામાં ઓછો ૮ અક્ષર, ૧ કેપિટલ, ૧ સ્મોલ, નંબર અને સ્પેશિયલ કેરેક્ટર હોવો જોઈએ'
                            }
                        })}
                    />

                    {/* Confirm Password */}
                    <Input
                        label="પાસવર્ડ ખાતરી કરો"
                        name="confirmPassword"
                        type="password"
                        placeholder="ફરીથી પાસવર્ડ દાખલ કરો"
                        icon={FiLock}
                        required
                        error={errors.confirmPassword}
                        {...register('confirmPassword', {
                            required: 'પાસવર્ડ ખાતરી કરવો ફરજિયાત છે',
                            validate: (val) => val === password || 'પાસવર્ડ એકસમાન નથી'
                        })}
                    />
                </div>

                {/* Accept Terms checkbox */}
                <div className="flex flex-col select-none">
                    <label className="flex items-start gap-2.5 cursor-pointer font-medium text-dark-light text-sm">
                        <input
                            type="checkbox"
                            className="w-4 h-4 mt-0.5 rounded text-primary focus:ring-primary border-dark/15 cursor-pointer"
                            {...register('acceptTerms', { required: 'નિયમો અને શરતોનો સ્વીકાર કરવો ફરજિયાત છે' })}
                        />
                        <span>હું નિયમો અને શરતોનો સ્વીકાર કરું છું (Accept Terms & Conditions)</span>
                    </label>
                    {errors.acceptTerms && (
                        <span className="text-xs text-red-600 font-semibold mt-1">
                            {errors.acceptTerms.message}
                        </span>
                    )}
                </div>

                {/* Register Button */}
                <Button type="submit" variant="primary" isLoading={isLoading} disabled={isLoading} className="mt-2">
                    ખાતું બનાવો (Register)
                </Button>

                {/* Already have an account */}
                <div className="text-center text-sm text-dark-light/95 pt-2 border-t border-dark/5">
                    <span>પહેલેથી જ ખાતું છે? </span>
                    <Link to="/farmer/login" className="text-primary font-bold hover:underline">
                        અહીં લોગિન કરો (Login here)
                    </Link>
                </div>
            </form>
        </FormContainer>
    )
}

export default FarmerRegister
