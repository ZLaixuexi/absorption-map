#include <stdio.h>
#include <math.h>
#include <fitsio.h>
#define  N 30  //interpo number of distance
  int isrf_index(int ir,
                 int iz,
                 int inu,
                 int icomp,
                 int nr,
                 int nz,
                 int nnu,
                 int ncomp) {

    return icomp*nnu*nz*nr + inu*nz*nr + iz*nr + ir;

  }

float cosine_theorem(float a, float b, float angle_C)
{
    float angle_C_radians = angle_C * M_PI / 180.;
    float c = sqrt(a*a + b*b - 2*a*b*cos(angle_C_radians));
    return c;
}

float lb2RZ(float l, float b, float L)
{
    float Rs = 8.0 ;// #sun2GC kpc
    float l_rad = l * M_PI / 180.;
    float b_rad = b * M_PI / 180.;
    float Z=L*sin(b_rad);
    float rou = L *cos(b_rad);// #shadow of star in galactic plane, to sun
    float R=0.;
    if( l_rad < M_PI)
       R = sqrt(Rs*Rs + rou*rou - 2*Rs*rou* cos(l_rad));
    else
       R = sqrt(Rs*Rs + rou*rou - 2*Rs*rou* cos(2*M_PI-l_rad));
    return R ;
}
//g++ all8_cmb_galprop_interpolation_argvZ.c  -o all8_cmb_galprop_interpolation_argvZ -I/home/lhaaso/jlzhang/cfitsio/cfitsio-3.49/include -lm -L/home/lhaaso/jlzhang/cfitsio/cfitsio-3.49/lib -lcfitsio
//./all8_cmb_galprop_interpolation_argvZ 8.95 79.8 3.34 2>&1 |tee all8_cmb_galprop_interpolation_argvZ_CygnusX3.txt
main(int argc, char *argv[])
{  
   if (argc < 4)
   {
      printf("USAGE: %s star2sun lon@GAL(l) lat@GAL(b)  !!!\n",argv[0]);
      exit(0);
   }
   float star2sun=atof(argv[1]), l=atof(argv[2]), b=atof(argv[3]); 
    
        double black[10000][2],blue[10000][2],kpc8[10000][2];
	FILE    *fp;
        float   n_isrf=0.;
        double  n_black=0,n_blue=0,n_kpc8=0,n_cmb=0,n=0;  
        double  n1=0;
        double a11=0,a22=0,a33=0;
        double P1=0;
	
	double  lightspeed=299792458 ; //c m/s
	double  planckconstant=6.62607015e-34 ; //h

	double  sigmaT=0.665;//barn   
	double  m=0.511; //electron matter MeV
	double  kpc=3.08568025*pow(10.0,-3.0); //kpc*10^-24
	double  sigmaPP=0.;
  	double  E1=0.;//2*pow(10.0,13.0);              //10TeV
	double  s;                          //s=4*E1*E2
	
	double c=1.329238*pow(10,13);         //cmb?
	double kt=2.726/(300*38.68149);
        double ncmb=0;

	
	double  x;
        double  x_start=0.10079055163712, x_ISRF=991.9018903579982, x_end=72*1e4; //cmb 72cm to unit um
	double  E2_start=12.3984198; //
	//double  E2_end=pow(10,-0.06856*x_end+1.09342);
	double  dx=(log10(x_ISRF)-log10(x_start))/10000;  //x_start=0., x_end=58.34 
        double  E2=E2_start;
        double  dE2=log(10)*dx; //from old code, 
	
	double  P=0.0;
        
	double  p;
	double  E;
        
        double a1,a2,a3;
	
	int i=0;
        int j=0;

        double cs,dcs=0.005;
        double logE1=-1;
	
    float n_optical=0., n_infrared=0.;	
    //float ir=0, iz=0; //
    //float ir=8, iz=0, d2sun=8.95;  //cygnus X-3 using ISRF @position ir and iz, integral L=d2sun
    //float ir=5., iz=0., d2sun=4.6 ; //SS433 
    
    float star2gc=0., m2gc=0., sun2gc=8.0;
    //float star2sun=8., l=0., sun2gc=8.0; //GC to sun, repeat my result astro-ph/0508236
    //float star2sun=4.6, l=39.7 ;  //SS433 
    //float star2sun=6.2, l=6.7 ;   //V4641 Sgr
    //float star2sun=9.4, l=45.3 ;   //GRS 1915+105
    //float star2sun=8.95, l=79.8 ;   //Cygnus X-3
    //float star2sun=2.2, l=71.3 ;   //Cygnus X-1
    //float star2sun=4.2, l=54.0 ;   //XTE J1859+226
    //float star2sun=1.7, l=157.7 ;  //XTE J1118+480 
    //float star2sun=4.1, l=149.2 ;  //CI Cam 
    //float star2sun=2.39, l=73.1 ; //V404 Cygni
    //float star2sun=3.5, l=35.8 ; //MAXI J1820+070
    
    //float star2sun=11.7, l=41.1 ; //J1859+083 11.7kpc
    //float star2sun=21.5, l=41.1 ; //J1859+083 21.5kpc


    float r_star=lb2RZ(l, b, star2sun);
    float r_middle=lb2RZ(l,b, star2sun/2.);

    int N1=ceil(star2sun/1.); //num of step in distance
    float delta_d=star2sun/N1; //step length

    //printf("N1: %d %f\n",N1,delta_d);
    //return 0;
    float ir[N]={0.};
    float iz[N]={0.};
    int irr[N]={0};
    int izz[N]={0};	
    float value[N][3]={0.};
    float n_value[N][3]={0.};
    float rr[N]={0.};
    float zz[N]={0.};

    int status = 0;

    char filename[150]="data/MilkyWay_DR0.5_DZ0.1_DPHI10_RMAX20_ZMAX5_galprop_format.fits.gz";
    //ref. CRPropagation/dragon/eloss.cc and galprop_v57_release/source/read_isrf.cc
    fitsfile *fptr = NULL;
    if ( fits_open_file(&fptr, filename, READONLY, &status) ) fits_report_error(stderr, status);

    int NAXIS, NAXIS1, NAXIS2, NAXIS3, NAXIS4;
    float CRVAL1,CRVAL2,CRVAL3,CDELT1,CDELT2,CDELT3;
    char comment[100];

    if( fits_read_key(fptr,TINT,"NAXIS" ,&NAXIS ,comment,&status) ) fits_report_error(stderr, status);
    if( fits_read_key(fptr,TINT,"NAXIS1",&NAXIS1,comment,&status) ) fits_report_error(stderr, status);
    if( fits_read_key(fptr,TINT,"NAXIS2",&NAXIS2,comment,&status) ) fits_report_error(stderr, status);
    if( fits_read_key(fptr,TINT,"NAXIS3",&NAXIS3,comment,&status) ) fits_report_error(stderr, status);
    if( fits_read_key(fptr,TINT,"NAXIS4",&NAXIS4,comment,&status) ) fits_report_error(stderr, status);

    if( fits_read_key(fptr,TFLOAT,"CRVAL1",&CRVAL1,comment,&status) ) fits_report_error(stderr, status);
    if( fits_read_key(fptr,TFLOAT,"CRVAL2",&CRVAL2,comment,&status) ) fits_report_error(stderr, status);
    if( fits_read_key(fptr,TFLOAT,"CRVAL3",&CRVAL3,comment,&status) ) fits_report_error(stderr, status);
    if( fits_read_key(fptr,TFLOAT,"CDELT1",&CDELT1,comment,&status) ) fits_report_error(stderr, status);
    if( fits_read_key(fptr,TFLOAT,"CDELT2",&CDELT2,comment,&status) ) fits_report_error(stderr, status);
    if( fits_read_key(fptr,TFLOAT,"CDELT3",&CDELT3,comment,&status) ) fits_report_error(stderr, status);

    int dimr_isrf = NAXIS1;
    int dimz_isrf = NAXIS2;
    int dimnu = NAXIS3;
    int ncomp = NAXIS4;

    long nelements=dimr_isrf*dimz_isrf*dimnu*ncomp;
    long felement=1;
    float *isrf_in = new float[nelements]();
    float nulval=0;
    int anynul;

    if( fits_read_img(fptr,TFLOAT,felement,nelements,&nulval,isrf_in,&anynul,&status) ) fits_report_error(stderr, status);

    if (fits_close_file(fptr, &status)) fits_report_error(stderr, status);

    for( int id=0; id<N1; id++)
    {     
          ir[id]=lb2RZ(l, b, delta_d/2.+id*delta_d);//the middle point in n ranges, to GC	  
          irr[id]=(int)((ir[id] -CRVAL1)/CDELT1+0.5);//IMOS20060420
          izz[id]=(int)((iz[id]-CRVAL2)/CDELT2+0.5);//IMOS20060420
          if(irr[id]>NAXIS1-2) irr[id]=NAXIS1-2;
          if(izz[id]>NAXIS2-2) izz[id]=NAXIS2-2;
          rr[id]=CRVAL1+irr[id]*CDELT1;
          zz[id]=CRVAL2+izz[id]*CDELT2;
    }
    //printf("ir[id] %f %f\n",ir[0],ir[N1-1]);
      // fp=fopen("all.data","w");
      //fp=fopen("all8_cmb_x3.txt","w");
      for(logE1=-1;logE1<=7.0;logE1+=0.1)   //s=2*E1*E2*(1-cs)
       {
         P=0;    // E1=?
	 P1=0.;
         n=ncmb=0;
         E1=pow(10,logE1);  
        // x_end=58.34; // all8 
	//printf("logE1 %lf %lf %lf\n",x_start, x_end,dx);
	for(i=1,x=x_start;x<x_end;x*=pow(10,dx))
	   {
             E2=1.23984198/x; //transfer from get points in figure to E, which is also wavelength. wavelength start, 1e-1 um is 12.4eV, E(eV)=1.2398/lamda(um)
	     int ix=(int)((log10(x) -CRVAL3)/CDELT3+0.5);
             //if(x<=32359.) //optical, infrared
	     if(ix<NAXIS3)
               {
		 for(int id=0; id<N1; id++) //3 distance: sun2gc, r_star,r_middle
		 {
		     for(int ic=0; ic<NAXIS4; ic++) //optical 0, infrared 1, CMB 2
		     {
                       float v1=isrf_in[isrf_index(irr[id]  ,izz[id]  ,ix,ic,NAXIS1,NAXIS2,NAXIS3,NAXIS4)];
                       float v2=isrf_in[isrf_index(irr[id+1],izz[id]  ,ix,ic,NAXIS1,NAXIS2,NAXIS3,NAXIS4)];
                       float v3=isrf_in[isrf_index(irr[id]  ,izz[id+1],ix,ic,NAXIS1,NAXIS2,NAXIS3,NAXIS4)];
                       float v4=isrf_in[isrf_index(irr[id+1],izz[id+1],ix,ic,NAXIS1,NAXIS2,NAXIS3,NAXIS4)];
                       float v5=v1+(v2-v1)*(ir[id]-rr[id])/CDELT1;
                       float v6=v3+(v4-v3)*(ir[id]-rr[id])/CDELT1;
                       value[id][ic]=v5+(v6-v5)*(iz[id]-zz[id])/CDELT2;
                       if(value[id][ic]<0.0) value[id][ic]=0.0;
                       n_value[id][ic]=value[id][ic]/E2;
		     }
		 }

               }  
             else //CMB region not in fits
               {
                ncmb=c*pow(E2,3)/(exp(E2/kt)-1);
               }

             n_isrf=0.;
             for(int id=0; id<N1; id++) //3 distance: sun2gc, r_star,r_middle
                {
                  for(int ic=0; ic<NAXIS4-1; ic++) //optical 0, infrared 1, CMB 2
                     {
                      n_isrf+=n_value[id][ic];
                     }
                 }

	    n=(n_isrf)/N1 + n_value[0][2]+ ncmb ; //n_value[0][2] is cmb
            //n=(n_isrf)/N1  ;  //ISRF only
	    //n=n_value[0][2]+ncmb; //CMB only
	   //printf("before %d %f %f %f %f %f %f %f %f\n",i, E1,E2,n,sigmaPP, x, n_blue,n_black,n_kpc8);
           for(j=0;j<200;j++)
             {
               cs=0.01*(j-99.5);  //cos
	       s=2*E1*E2*(1-cs);//2*E1*E2/pow(10,12)*(1-cs);
	       if(s>4*m*m)
	         {
	           p=sqrt(s/4-m*m);
	           E=sqrt(s)/2;    
	           sigmaPP=sigmaT*(3*m*m/(4*s))*(p/E)*(-2-2*m*m/(E*E)+(2*E/p+2*m*m/(E*p)-m*m*m*m/(E*E*E*p))*log((E+p)*(E+p)/(m*m)));  
	           P+=sigmaPP*n*star2sun*kpc*dE2*dcs;
                   //P1+=sigmaPP*n1*8*kpc*dE2*dcs;
	           // fprintf(fp,"%f %f\n",s,sigmaPP);
	         }
             }
	   //printf("after %f %f %f %f\n",E1,E2,n,sigmaPP);
        }	     
	//printf("logE1 %f %f %f %f %f\n",logE1, sigmaPP, n , dE2, dcs);
       //fprintf(fp,"%.12lf %.12lf\n",logE1,1-exp(-P));
       //fprintf(fp,"%.12lf %.12lf\n",E1,P);
       //printf("%.12lf %.12lf\n",logE1,1-exp(-P));
       //fprintf(fp,"%.12lf %.12lf\n",E1,P1);
       printf("%.12lf %.12lf\n",E1,exp(-P));
       //printf("%.12lf %.12lf\n",E1,exp(-P1));
       //printf("E1:%f P:%f\n",E1,P);
     }
    //fclose(fp);
}	
