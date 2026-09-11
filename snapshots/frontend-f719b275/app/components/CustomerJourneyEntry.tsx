'use client'

// P4.4B: the persistent bottom-right floating CTA has been removed.
// The PRIMARY conversion moment is now the in-conversation Professional
// Handoff card (see ChatComponent + ProfessionalHandoffCard), which appears
// only when the AI has gathered enough structured information.
import ChatComponent from './ChatComponent'
import MatterRuntimeBridge from './MatterRuntimeBridge'
import './butler-workspace.css'

export default function CustomerJourneyEntry() {
  return (
    <>
      <MatterRuntimeBridge />
      <ChatComponent butlerMode />
    </>
  )
}
