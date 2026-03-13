import type { FC } from 'react';
import type { Source, Status } from '../components/Card/Card';
import type { IconProps } from '../components/icons/IconProps';
import DocsIcon from '../components/icons/DocsIcon/DocsIcon';
import ScriptIcon from '../components/icons/ScriptIcon/ScriptIcon';
import ExpertIcon from '../components/icons/ExpertIcon/ExpertIcon';

interface TagData {
    Icon: FC<IconProps>;
    label: string;
}


export const getSourceProps = (source: Source): TagData => {
    switch (source) {
        case 'docs':
            return {
                Icon: DocsIcon,
                label: 'Documents',
            };
        case 'script':
            return {
                Icon: ScriptIcon,
                label: 'Script',
            };
        case 'expert':
            return {
                Icon: ExpertIcon,
                label: 'Expert',
            };
        case 'new_doc':
            return {
                Icon: DocsIcon,
                label: 'New Doc',
            };
    }
};

export const getStatusProps = (status: Status): TagData => {
    switch (status) {
        case 'pending':
            return {
                Icon: DocsIcon,
                label: 'Pending Answer',
            };
        case 'resolved':
            return {
                Icon: ScriptIcon,
                label: 'Resolved',
            };
        case 'rejected':
            return {
                Icon: ExpertIcon,
                label: 'Rejected',
            };
    }
};

