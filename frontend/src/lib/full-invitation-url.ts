export default function fullInvitationUrl(token: string) {
  return `${window.location.origin}/invitation?token=${token}`;
}
