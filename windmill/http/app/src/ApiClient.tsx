import axios, { Method } from "axios";

const BaseURI = "http://localhost:8000";

const client = axios.create({
  baseURL: BaseURI,
  data: JSON
});

export class APIClient {
  public getOperators() {
    return this.perform("GET", "/v1/operators");
  }

  async perform(method: Method, resource: string, data?: any) {
    return client({
      method,
      url: resource,
      data
      //   headers: {
      //     Authorization: `Bearer ${this.accessToken}`
      //   }
    }).then(resp => {
      return resp.data ? resp.data : [];
    });
  }
}