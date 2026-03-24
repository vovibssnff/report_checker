import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { observer } from 'mobx-react-lite';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { authStore } from '../store/authStore';
import InputField from '../components/ImputField/InputField';
import Button from '../components/Button/Button';

const AuthPage: React.FC = observer(() => {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [name, setName] = useState('');

  const { login, loading, error } = authStore;

  const setLang = (lng: 'en' | 'ru') => {
    i18n.changeLanguage(lng);
    if (typeof localStorage !== 'undefined') localStorage.setItem('lang', lng);
  };

  useEffect(() => {
    // Keep language consistent after refresh.
    if (typeof localStorage === 'undefined') return;
    const saved = localStorage.getItem('lang');
    if (saved === 'en' || saved === 'ru') i18n.changeLanguage(saved);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login({ email, name });
      navigate('/', { replace: true });
    } catch {
      // error is shown below
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-white px-4">
      <div className="w-full max-w-md p-4">
        <div className="absolute top-4 right-4 flex gap-2 text-sm">
          <button
            type="button"
            onClick={() => setLang('ru')}
            className={`px-2 py-1 rounded ${i18n.language === 'ru' ? 'font-medium text-black underline' : 'text-gray-500 hover:text-gray-700'}`}
          >
            RU
          </button>
          <button
            type="button"
            onClick={() => setLang('en')}
            className={`px-2 py-1 rounded ${i18n.language === 'en' ? 'font-medium text-black underline' : 'text-gray-500 hover:text-gray-700'}`}
          >
            EN
          </button>
        </div>

        <AnimatePresence mode="wait">
          <motion.div
            key="auth"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
            className="flex flex-col"
          >
            <div className="flex flex-col gap-2 mb-10 px-4">
              <h1 className="text-2xl">{t('auth.signIn')}</h1>
              <p className="text-sm text-gray-500">{t('auth.signInSubtitle')}</p>
            </div>

            <form onSubmit={handleSubmit} className="flex flex-col gap-8">
              <div className="flex flex-col gap-4">
                <InputField label={t('auth.name')} value={name} onChange={setName} required />
                <InputField label={t('auth.email')} type="email" value={email} onChange={setEmail} required />
              </div>

              {error ? <p className="text-sm text-red-600 px-2 -mt-4">{error}</p> : null}

              <Button type="submit" disabled={loading} fullWidth size="l">
                {loading ? t('auth.signingIn') : t('auth.signIn')}
              </Button>
            </form>
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
});

export default AuthPage;
