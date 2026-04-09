import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { observer } from 'mobx-react-lite';
import { motion, AnimatePresence } from 'framer-motion';
import useEmblaCarousel from 'embla-carousel-react';
import { useTranslation } from 'react-i18next';
import { authStore } from '../store/authStore';
import InputField from '../components/ImputField/InputField';
import Button from '../components/Button/Button';
import { GraduationCap, BookOpen } from 'lucide-react';

type UserRole = 'student' | 'teacher';

type AuthMode = 'login' | 'register';

const AuthPage: React.FC = observer(() => {
  const { t, i18n } = useTranslation();
  const location = useLocation();
  const [mode, setMode] = useState<AuthMode>(() =>
    location.pathname === '/register' ? 'register' : 'login'
  );
  const [registerStep, setRegisterStep] = useState(0);

  useEffect(() => {
    setMode(location.pathname === '/register' ? 'register' : 'login');
  }, [location.pathname]);

  useEffect(() => {
    // Keep language consistent after refresh.
    if (typeof localStorage === 'undefined') return;
    const saved = localStorage.getItem('lang');
    if (saved === 'en' || saved === 'ru') i18n.changeLanguage(saved);
  }, [i18n]);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [name, setName] = useState('');
  const [role, setRole] = useState<UserRole | null>(null);

  const navigate = useNavigate();
  const { login, register, loginWithItmo, fetchAuthMode, loading, error } = authStore;

  const [emblaRef, emblaApi] = useEmblaCarousel({
    loop: false,
    duration: 16,
    watchDrag: false,
  });

  useEffect(() => {
    if (emblaApi) emblaApi.scrollTo(registerStep);
  }, [emblaApi, registerStep]);

  const setLang = (lng: 'en' | 'ru') => {
    i18n.changeLanguage(lng);
    if (typeof localStorage !== 'undefined') localStorage.setItem('lang', lng);
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login({ email, password });
      navigate('/', { replace: true });
    } catch {
      // error is shown below
    }
  };

  const handleItmoIdClick = () => {
    void loginWithItmo();
  };

  const handleRegisterSubmit = async () => {
    if (password !== passwordConfirm || !name.trim() || !email.trim() || !password || !role) return;
    try {
      await register({ email, name, password, role });
      navigate('/', { replace: true });
    } catch {
      // error is shown below
    }
  };

  const switchMode = () => {
    setMode((m) => (m === 'login' ? 'register' : 'login'));
    setRegisterStep(0);
    setPasswordConfirm('');
  };

  const passwordsMatch = password === passwordConfirm;
  const registerStep0Valid = name.trim() && email.trim() && role !== null;
  const canGoStep1 = registerStep0Valid;
  const canSubmitRegister = registerStep === 1 && password.length > 0 && passwordsMatch && !loading;
  const itmoOnlyAuth = authStore.authMode === 'itmo_id';

  useEffect(() => {
    void fetchAuthMode();
  }, [fetchAuthMode]);

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
          {itmoOnlyAuth ? (
            <motion.div
              key="itmo-login"
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
              <div className="flex flex-col gap-8">
                {error ? <p className="text-sm text-red-600 px-2 -mt-4">{error}</p> : null}
                <Button
                  type="button"
                  typeStyle="secondary"
                  fullWidth
                  size="l"
                  onClick={handleItmoIdClick}
                  disabled={loading}
                >
                  {t('auth.signInWithItmo')}
                </Button>
              </div>
            </motion.div>
          ) : mode === 'login' ? (
            <motion.div
              key="login"
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
              <form onSubmit={handleLogin} className="flex flex-col gap-8">
                <div className="flex flex-col gap-4">
                  <InputField label={t('auth.email')} type="email" value={email} onChange={setEmail} required />
                  <InputField label={t('auth.password')} type="password" value={password} onChange={setPassword} required />
                </div>
                {error ? <p className="text-sm text-red-600 px-2 -mt-4">{error}</p> : null}
                <Button type="submit" disabled={loading} fullWidth size="l">
                  {loading ? t('auth.signingIn') : t('auth.signIn')}
                </Button>
                <div className="h-px bg-gray-200 w-full relative"><div className="h-fit w-fit px-4 bg-white absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 text-sm text-gray-500">Или</div></div>
                <Button
                  type="button"
                  typeStyle="secondary"
                  fullWidth
                  size="l"
                  onClick={handleItmoIdClick}
                >
                  {t('auth.signInWithItmo')}
                </Button>
              </form>
            </motion.div>
          ) : (
            <motion.div
              key="register"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.2 }}
              className="flex flex-col relative min-h-[320px]"
            >
              <div className="embla overflow-hidden flex-1 min-h-0 p-4" ref={emblaRef}>
                <div className="embla__container flex h-full">
                  <div
                    className={`embla__slide transition-all duration-200 ${
                      registerStep !== 0 ? 'opacity-0 pointer-events-none' : ''
                    }`}
                  >
                    <div className="flex flex-col gap-2 mb-10 px-4">
                      <h1 className="text-2xl">{t('auth.getAcquainted')}</h1>
                      <p className="text-sm text-gray-500">{t('auth.getAcquaintedSubtitle')}</p>
                    </div>
                    <div className="flex flex-col gap-4">
                      <div className="grid grid-cols-2 gap-3 pb-2">
                        {(['student', 'teacher'] as const).map((r) => (
                          <button
                            key={r}
                            type="button"
                            onClick={() => setRole(r)}
                            className={`flex flex-row items-center gap-3 p-4 text-left rounded-full border transition-all ${
                              role === r
                                ? 'border-black bg-black/3'
                                : 'border-[rgba(0,0,0,0.08)] hover:border-[rgba(0,0,0,0.2)]'
                            }`}
                          >
                            {r === 'student'
                              ? <GraduationCap className={`size-5 ${role === r ? 'text-black' : 'text-gray-400'}`} />
                              : <BookOpen className={`size-5 ${role === r ? 'text-black' : 'text-gray-400'}`} />
                            }
                            <span className={`text-sm font-medium ${role === r ? 'text-black' : 'text-gray-500'}`}>
                              {t(`auth.${r}`)}
                            </span>
                          </button>
                        ))}
                      </div>
                      <InputField label={t('auth.name')} value={name} onChange={setName} required />
                      <InputField label={t('auth.email')} type="email" value={email} onChange={setEmail} required />
                    </div>
                  </div>
                  <div
                    className={`embla__slide transition-all duration-200 ${
                      registerStep !== 1 ? 'opacity-0 pointer-events-none' : ''
                    }`}
                  >
                    <div className="flex flex-col gap-2 mb-10 px-4">
                      <h1 className="text-2xl">{t('auth.createPassword')}</h1>
                      <p className="text-sm text-gray-500">{t('auth.createPasswordSubtitle')}</p>
                    </div>
                    <div className="flex flex-col gap-4">
                      <InputField
                        label={t('auth.password')}
                        type="password"
                        value={password}
                        onChange={setPassword}
                        required
                      />
                      <InputField
                        label={t('auth.confirmPassword')}
                        type="password"
                        value={passwordConfirm}
                        onChange={setPasswordConfirm}
                        required
                      />
                      {passwordConfirm.length > 0 && !passwordsMatch && (
                        <p className="text-xs text-red-500">{t('auth.passwordsDoNotMatch')}</p>
                      )}
                      {error ? <p className="text-sm text-red-600">{error}</p> : null}
                    </div>
                  </div>
                </div>
              </div>
              <div className="flex items-center justify-between mt-6 pt-4 px-8">
                <p className="text-sm text-gray-500">{t('auth.step', { current: registerStep + 1, total: 2 })}</p>
                <div className="flex gap-2">
                  {registerStep > 0 && (
                    <Button type="button" typeStyle="secondary" size="s" onClick={() => setRegisterStep(0)}>
                      {t('auth.back')}
                    </Button>
                  )}
                  {registerStep < 1 ? (
                    <Button
                      type="button"
                      size="s"
                      disabled={!canGoStep1}
                      onClick={() => setRegisterStep(1)}
                    >
                      {t('auth.next')}
                    </Button>
                  ) : (
                    <Button
                      type="button"
                      size="s"
                      disabled={!canSubmitRegister}
                      onClick={handleRegisterSubmit}
                    >
                      {loading ? t('auth.creatingAccount') : t('auth.register')}
                    </Button>
                  )}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        {!itmoOnlyAuth ? (
          <motion.p
            className="mt-6 text-center text-sm text-gray-600"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.1 }}
          >
            {mode === 'login' ? (
              <>
                {t('auth.noAccount')}{' '}
                <button type="button" onClick={switchMode} className="text-black font-medium underline hover:no-underline">
                  {t('auth.registerLink')}
                </button>
              </>
            ) : (
              <>
                {t('auth.haveAccount')}{' '}
                <button type="button" onClick={switchMode} className="text-black font-medium underline hover:no-underline">
                  {t('auth.signInLink')}
                </button>
              </>
            )}
          </motion.p>
        ) : null}
      </div>
    </div>
  );
});

export default AuthPage;
