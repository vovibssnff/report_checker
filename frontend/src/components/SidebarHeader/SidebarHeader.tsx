import React from 'react';
import { observer } from 'mobx-react-lite';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Avatar from '../Avatar/Avatar';
import IconTextButton from '../IconTextButton/IconTextButton';
import LogoutIcon from '../icons/LogoutIcon/LogoutIcon';
import { authStore } from '../../store/authStore';

const SidebarHeader: React.FC = observer(() => {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const { user, logout } = authStore;

  const handleLogout = async () => {
    await logout();
    navigate('/login', { replace: true });
  };

  const displayName = user?.name?.trim() || user?.email || '';

  return (
    <div className="p-4 flex flex-row gap-2 items-center justify-between min-w-0 w-full">
      <div className="flex items-center gap-3 min-w-0">
        <Avatar name={displayName} size="sm" />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-gray-600 truncate" title={user?.email}>
            {displayName || '—'}
          </p>
          {user?.organization ? (
            <p className="text-xs text-gray-400 truncate">{user.organization}</p>
          ) : null}
        </div>
      </div>
      <div className="flex items-center gap-1">
        <button
          type="button"
          onClick={() => { i18n.changeLanguage('ru'); localStorage.setItem('lang', 'ru'); }}
          className={`text-xs px-1.5 py-0.5 rounded ${i18n.language === 'ru' ? 'font-medium text-black bg-gray-100' : 'text-gray-400 hover:text-gray-600'}`}
        >
          RU
        </button>
        <button
          type="button"
          onClick={() => { i18n.changeLanguage('en'); localStorage.setItem('lang', 'en'); }}
          className={`text-xs px-1.5 py-0.5 rounded ${i18n.language === 'en' ? 'font-medium text-black bg-gray-100' : 'text-gray-400 hover:text-gray-600'}`}
        >
          EN
        </button>
        <IconTextButton
          icon={<LogoutIcon size="1rem" />}
          onClick={handleLogout}
          className="justify-start text-gray-500 hover:text-black w-fit aspect-square p-3"
          aria-label={t('common.logout')}
        >
        </IconTextButton>
      </div>
    </div>
  );
});

export default SidebarHeader;
