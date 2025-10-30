export interface PhoneData {
  phone: string;
  apiId: number;
  apiHash: string;
  session?: string;
  phoneCodeHash?: string;
  verified: boolean;
  lastAuthAt?: string;
}
