"use client";

import { memo } from 'react';
import Script from "next/script";

const ElevenLabsWidget = memo(() => {
    return (
        <>
            {/* ElevenLabs Voice Assistant Widget */}
            <div id="elevenlabs-widget" dangerouslySetInnerHTML={{ __html: `<elevenlabs-convai agent-id=\"agent_01jzafryw2fmpbg8pfm6q1apc1\"></elevenlabs-convai>` }} />
            <Script src="https://unpkg.com/@elevenlabs/convai-widget-embed" async strategy="afterInteractive" />
        </>
    );
});

ElevenLabsWidget.displayName = 'ElevenLabsWidget';

export default ElevenLabsWidget;
