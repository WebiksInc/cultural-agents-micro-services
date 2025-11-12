export interface PollOption {
  text: string;
  voterCount: number;
  chosen: boolean;
}

export interface Poll {
  messageId: number;
  pollId: string;
  question: string;
  date: string;
  closed: boolean;
  multipleChoice: boolean;
  quiz: boolean;
  options: PollOption[];
  totalVoters: number;
  recentVoters?: string[];
  closePeriod?: number;
  closeDate?: string;
}

export interface GetPollsParams {
  phone: string;
  chatId: string;
  limit: number;
}

export interface GetPollsResponse {
  success: true;
  chatId: string;
  chatTitle: string;
  phone: string;
  pollsCount: number;
  polls: Poll[];
}

export interface VotePollRequest {
  phone: string;
  chatId: string;
  messageId: number;
  optionIds: number[];
}

export interface VotePollResponse {
  success: true;
  pollId: string;
  messageId: number;
  votedOptions: number[];
}
