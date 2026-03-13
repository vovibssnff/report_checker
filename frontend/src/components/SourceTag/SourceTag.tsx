import React from 'react';
import './SourceTag.css';
import type { Source } from '../Card/Card';
import { getSourceProps } from '../../utils/render';

interface SourceTagProps {
  className?: string;
  source: Source;
  compact?: boolean;
}

const SourceTag: React.FC<SourceTagProps> = (props) => {
  const { Icon, label } = getSourceProps(props.source);

  const finalClassName = `source-tag ${props.compact ? 'w-7 h-7 outline-white outline-4 bg-[rgb(242,242,242)]' : 'w-fit h-fit'} rounded-[2rem] flex row gap-[6px] items-center justify-center -mr-1 ` + (props.className || '');
  return (
    <div className={finalClassName}>
      <Icon size='0.75rem' fill={'#000000'} className='opacity-80' />
      {!props.compact && <p className='text-xs'>{label}</p>}
    </div>
  );
};

export default SourceTag;
