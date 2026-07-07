'use client';

import { useState, useRef, useEffect } from 'react';
import styles from './page.module.css';

type Message = {
  id: string;
  sender: 'user' | 'bot';
  text: string;
};

type GapAnalysis = {
  current_eligibility_score: number;
  potential_eligibility_score: number;
  gap_percentage: number;
  total_potential_benefit_unlocked: number;
  top_improvements: Array<{
    parameter: string;
    action: string;
    estimated_effort: string;
    impact_type: string;
    schemes_unlocked_count: number;
  }>;
};

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const [intents, setIntents] = useState<string[]>([]);
  const [profile, setProfile] = useState<Record<string, any>>({});
  const [currentQuestionParam, setCurrentQuestionParam] = useState<string | null>(null);
  
  const [gapAnalysis, setGapAnalysis] = useState<GapAnalysis | null>(null);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [showDashboard, setShowDashboard] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const addMessage = (text: string, sender: 'user' | 'bot') => {
    setMessages(prev => [...prev, { id: Math.random().toString(), text, sender }]);
  };

  const submitQuery = async (queryText: string) => {
    if (!queryText.trim()) return;
    
    addMessage(queryText, 'user');
    setInput('');
    setIsLoading(true);

    try {
      if (intents.length === 0) {
        const intentRes = await fetch('/api/chat/intent', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: queryText })
        });
        const intentData = await intentRes.json();
        
        if (intentData.status === 'clarification_needed') {
          addMessage(intentData.message, 'bot');
          setIsLoading(false);
          return;
        }
        
        const newIntents = intentData.intents;
        setIntents(newIntents);
        addMessage(`I understand you're looking for: ${newIntents.join(', ')}. Let's see what you're eligible for.`, 'bot');
        
        fetchNextQuestion(newIntents, profile);
      } 
      else if (currentQuestionParam) {
        let val: any = queryText;
        const textLower = queryText.toLowerCase();
        if (textLower === 'yes') val = true;
        else if (textLower === 'no') val = false;
        else if (!isNaN(Number(queryText))) val = Number(queryText);
        
        // Strip the "business." prefix so the backend can nest it correctly
        const paramKey = currentQuestionParam.startsWith('business.') ? currentQuestionParam.replace('business.', '') : currentQuestionParam;
        const newProfile = { ...profile, [paramKey]: val };
        
        setProfile(newProfile);
        setCurrentQuestionParam(null);
        
        fetchNextQuestion(intents, newProfile);
      }
    } catch (error) {
      console.error(error);
      addMessage("Sorry, I encountered an error connecting to the engine.", 'bot');
      setIsLoading(false);
    }
  };

  const handleSend = () => {
    submitQuery(input);
  };

  const fetchNextQuestion = async (currentIntents: string[], currentProfile: Record<string, any>) => {
    try {
      const qRes = await fetch('/api/chat/question', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ intents: currentIntents, profile: currentProfile })
      });
      const qData = await qRes.json();
      
      if (qData.status === 'question') {
        setCurrentQuestionParam(qData.parameter);
        addMessage(qData.question, 'bot');
        setIsLoading(false);
      } else {
        await fetchRecommendationsAndGaps(currentProfile);
      }
    } catch (error) {
      console.error(error);
      setIsLoading(false);
    }
  };

  const fetchRecommendationsAndGaps = async (currentProfile: Record<string, any>) => {
    try {
      const formattedProfile = Object.keys(currentProfile).reduce((acc, key) => {
        const k = key.startsWith('business.') ? key.replace('business.', '') : key;
        acc[k] = currentProfile[key];
        return acc;
      }, {} as Record<string, any>);

      const recRes = await fetch('/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formattedProfile)
      });
      
      if (recRes.ok) {
        const recData = await recRes.json();
        const eligibleSchemes = recData.filter((r: any) => r.is_eligible);
        setRecommendations(eligibleSchemes);
        
        if (eligibleSchemes.length > 0) {
            const schemeNames = eligibleSchemes.map((r: any) => r.scheme.scheme.name).join(", ");
            addMessage(`Great news! Based on your profile, you are eligible for the following schemes:\n\n${schemeNames}`, 'bot');
        } else {
            addMessage(`Based on your current profile, you are not immediately eligible for our top schemes. However, there are steps you can take.`, 'bot');
        }
      }

      const gapRes = await fetch('/api/gap_analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formattedProfile)
      });
      
      if (gapRes.ok) {
         const gapData = await gapRes.json();
         setGapAnalysis(gapData);
         setShowDashboard(true);
         
         if (gapData.top_improvements && gapData.top_improvements.length > 0) {
             addMessage(`I have analyzed your profile for missing requirements. Check the sidebar for suggestions on how you can unlock ${gapData.top_improvements[0].schemes_unlocked_count} more schemes!`, 'bot');
         }
      }
    } catch (error) {
      console.error("Analysis error", error);
    } finally {
      setIsLoading(false);
    }
  };

  const inputBar = (
    <div className={styles.emptyStateInputWrapper}>
      <div className={styles.centeredInputBox}>
        <div className={styles.plusIcon}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
        </div>
        <input 
          type="text" 
          className={styles.centeredInputField}
          placeholder="Ask anything" 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          disabled={isLoading}
          autoFocus
        />
        <div className={styles.micIcon}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
            <line x1="12" y1="19" x2="12" y2="22"></line>
          </svg>
        </div>
        <div className={styles.voiceButton} onClick={handleSend} style={{ cursor: input.trim() ? 'pointer' : 'default', opacity: input.trim() ? 1 : 0.5 }}>
          {input.trim() ? (
             <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
               <line x1="12" y1="19" x2="12" y2="5"></line>
               <polyline points="5 12 12 5 19 12"></polyline>
             </svg>
          ) : (
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2v20M17 5v14M7 5v14M22 9v6M2 9v6" />
            </svg>
          )}
        </div>
      </div>
    </div>
  );

  return (
    <div className={styles.appContainer}>
      
      <div className={styles.topNav}>
        FS Engine <span className={styles.caret}>&#709;</span>
      </div>

      {showDashboard && (
        <div className={styles.sidebar}>
          <div className={styles.sidebarHeader}>
            <div className={styles.avatarBot} style={{ width: '24px', height: '24px', fontSize: '0.8rem' }}>FS</div>
            Gap Analysis
          </div>
          <div className={styles.sidebarContent}>
            {gapAnalysis ? (
              <>
                <div className={styles.scoreCard}>
                  <h3>Eligibility Score</h3>
                  <div className={styles.scoreValue}>{gapAnalysis.current_eligibility_score}%</div>
                </div>

                <div>
                  <h3 style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Top Actions</h3>
                  {gapAnalysis.top_improvements.length > 0 ? (
                    gapAnalysis.top_improvements.slice(0, 4).map((imp, idx) => (
                      <div key={idx} className={styles.actionItem}>
                        <h4>{imp.action}</h4>
                        <p>Unlocks {imp.schemes_unlocked_count} schemes</p>
                      </div>
                    ))
                  ) : (
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>You are fully optimized!</p>
                  )}
                </div>
              </>
            ) : null}
          </div>
        </div>
      )}

      {messages.length === 0 ? (
        <div className={styles.emptyStateContainer}>
          <h1 className={styles.emptyStateTitle}>Where should we begin?</h1>
          
          {inputBar}
          
          <div className={styles.suggestionsRow}>
            <button className={styles.suggestionChip} onClick={() => submitQuery("I need working capital")}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
              I need working capital
            </button>
            <button className={styles.suggestionChip} onClick={() => submitQuery("Money for buying machinery")}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg>
              Money for buying machinery
            </button>
            <button className={styles.suggestionChip} onClick={() => submitQuery("Looking for business expansion")}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
              Looking for business expansion
            </button>
          </div>
        </div>
      ) : (
        <div className={styles.mainArea}>
          <div className={styles.chatContainer}>
            {messages.map((m) => (
              <div key={m.id} className={styles.messageRow}>
                <div className={styles.messageContent}>
                  <div className={`${styles.avatar} ${m.sender === 'user' ? styles.avatarUser : styles.avatarBot}`}>
                    {m.sender === 'user' ? 'U' : 'FS'}
                  </div>
                  <div className={styles.messageText} style={{ whiteSpace: 'pre-wrap' }}>
                    {m.text}
                  </div>
                </div>
              </div>
            ))}
            {isLoading && (
              <div className={styles.messageRow}>
                <div className={styles.messageContent}>
                  <div className={`${styles.avatar} ${styles.avatarBot}`}>FS</div>
                  <div className={styles.messageText} style={{ opacity: 0.5 }}>...</div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className={styles.inputContainer}>
             {inputBar}
          </div>
        </div>
      )}
    </div>
  );
}
